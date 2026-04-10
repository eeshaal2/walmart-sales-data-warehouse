
# Eeshaal Adeel
# 23i-2500
# DS-5C

import threading
import queue
import time
import pandas as pd
import mysql.connector
from mysql.connector import Error
import getpass
from collections import defaultdict
from datetime import date, datetime, timedelta
import sys
import traceback

HASH_TABLE_SLOTS = 10000    
DISK_BUFFER_SIZE = 500     
BATCH_INSERT_SIZE = 500
STREAM_BUFFER_MAX = HASH_TABLE_SLOTS * 2
PRODUCT_CACHE_REFRESH_SEC = 600
STREAM_CHUNK_SIZE = 200     
STREAM_DELAY = 0.0          
ENTRY_TTL_SECONDS = 60 * 60 * 24  

TRANSACTIONAL_CSV = "transactional_data.csv"
CUSTOMER_CSV = "customer_master_data.csv"
PRODUCT_CSV = "product_master_data.csv"

# THREAD SAFE STRUCTURES
stream_buffer = queue.Queue(maxsize=STREAM_BUFFER_MAX)
available_slots = HASH_TABLE_SLOTS
available_slots_lock = threading.Lock()
stream_finished = threading.Event()

# Hash table 
hash_table = defaultdict(list)
hash_lock = threading.Lock()

# Doubly-linked list for FIFO order with random deletions
class DLLNode:
    __slots__ = ("key", "prev", "next", "timestamp")
    def __init__(self, key):
        self.key = key
        self.prev = None
        self.next = None
        self.timestamp = time.time()

class DoublyLinkedQueue:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
        self.lock = threading.Lock()

    def append(self, node: DLLNode):
        with self.lock:
            if self.tail is None:
                self.head = self.tail = node
            else:
                node.prev = self.tail
                node.next = None
                self.tail.next = node
                self.tail = node
            self.size += 1

    def popleft(self):
        with self.lock:
            if self.head is None:
                return None
            node = self.head
            if node.next:
                self.head = node.next
                self.head.prev = None
            else:
                self.head = self.tail = None
            node.prev = node.next = None
            self.size -= 1
            return node

    def remove(self, node):
        with self.lock:
            if node is None:
                return
            if node.prev:
                node.prev.next = node.next
            else:
                self.head = node.next
            if node.next:
                node.next.prev = node.prev
            else:
                self.tail = node.prev
            node.prev = node.next = None
            self.size -= 1

    def peek_oldest(self):
        with self.lock:
            return self.head

    def __len__(self):
        with self.lock:
            return self.size

stream_queue = DoublyLinkedQueue()

# ----------------------
# PRODUCT PRICE CACHE
# ----------------------
product_prices = {}
product_cache_lock = threading.Lock()
product_cache_last_refresh = 0

# ----------------------
# DB helpers
# ----------------------
def connect_db_prompt():
    print("Enter DB connection details (MySQL).")
    host = input("Host [localhost]: ").strip() or "localhost"
    user = input("User [root]: ").strip() or "root"
    password = getpass.getpass("Password: ")
    dbname = input("Database [walmart_dw]: ").strip() or "walmart_dw"
    try:
        conn = mysql.connector.connect(host=host, user=user, password=password, database=dbname)
        if conn.is_connected():
            print("Connected to DB:", host, dbname)
            return conn
    except Exception as e:
        print("DB connection error:", e)
    return None

# DIM LOADERS
def load_customer_dim(conn, csv_path=CUSTOMER_CSV):
    print("[Loader] Loading dim_customer from", csv_path)
    cur = conn.cursor()
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print("Customer CSV not found:", csv_path)
        return
    # iterate and insert (INSERT IGNORE)
    rows = []
    for _, r in df.iterrows():
        try:
            cust_id = int(r['Customer_ID'])
        except:
            continue
        rows.append((
            cust_id,
            r.get('Gender'),
            str(r.get('Age')),
            r.get('Occupation'),
            r.get('City_Category'),
            str(r.get('Stay_In_Current_City_Years')),
            1 if int(r.get('Marital_Status', 0)) else 0
        ))
    # batch insert
    chunk = 0
    while chunk * 500 < len(rows):
        cur.executemany(
            "INSERT IGNORE INTO dim_customer (customer_id, gender, age, occupation, city_category, stay_in_current_city_years, marital_status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            rows[chunk*500:(chunk+1)*500]
        )
        chunk += 1
    conn.commit()
    cur.close()
    print("[Loader] dim_customer loaded:", len(rows))

def load_product_dim(conn, csv_path=PRODUCT_CSV):
    print("[Loader] Loading dim_product + dim_store + dim_supplier from", csv_path)
    cur = conn.cursor()
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print("Product CSV not found:", csv_path)
        return
    
    prod_rows = []
    store_rows = {}
    supplier_rows = {}
    
    for _, r in df.iterrows():
        pid = str(r['Product_ID'])
        # parse price$ -> float
        price_raw = str(r.get('price$', '')).strip()
        if price_raw.startswith('$'):
            price_val = float(price_raw.replace('$', '').replace(',', '').strip())
        else:
            try:
                price_val = float(price_raw)
            except:
                price_val = 0.0
        
        # We still collect all 5 values here to populate store/supplier dicts,
        # but we will only use the first 3 for the dim_product insert.
        prod_rows.append((pid, r.get('Product_Category'), price_val, int(r['storeID']), int(r['supplierID'])))
        store_rows[int(r['storeID'])] = r.get('storeName')
        supplier_rows[int(r['supplierID'])] = r.get('supplierName')

    # insert stores
    stores_list = [(k, v) for k, v in store_rows.items()]
    if stores_list:
        cur.executemany("INSERT IGNORE INTO dim_store (store_id, store_name) VALUES (%s, %s)", stores_list)

    # insert suppliers
    suppliers_list = [(k, v) for k, v in supplier_rows.items()]
    if suppliers_list:
        cur.executemany("INSERT IGNORE INTO dim_supplier (supplier_id, supplier_name) VALUES (%s, %s)", suppliers_list)

    # insert products -- UPDATED FOR STAR SCHEMA
    # We now slice the row to take only the first 3 elements (id, category, price)
    chunk = 0
    while chunk * 500 < len(prod_rows):
        # Select only the first 3 columns from the tuple
        batch_data = [row[:3] for row in prod_rows[chunk*500:(chunk+1)*500]]
        
        cur.executemany(
            "INSERT IGNORE INTO dim_product (product_id, product_category, price) VALUES (%s,%s,%s)",
            batch_data
        )
        chunk += 1

    conn.commit()
    cur.close()
    print("[Loader] dim_product + dim_store + dim_supplier loaded:", len(prod_rows))

def populate_dim_date(conn, start_date=date(2010,1,1), end_date=date(2030,12,31)):
    print("[Loader] Populating dim_date ...")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM dim_date")
    cnt = cur.fetchone()[0]
    if cnt > 0:
        print("[Loader] dim_date already populated (rows=%s)." % cnt)
    else:
        d = start_date
        inserts = []
        did = 1
        while d <= end_date:
            inserts.append((int(d.strftime("%Y%m%d")), d.strftime("%Y-%m-%d"), d.day, d.month, (d.month-1)//3+1, d.year, d.strftime("%A")))
            d += timedelta(days=1)
            if len(inserts) >= 500:
                cur.executemany("INSERT IGNORE INTO dim_date (date_id, full_date, day, month, quarter, year, weekday) VALUES (%s,%s,%s,%s,%s,%s,%s)", inserts)
                inserts = []
        if inserts:
            cur.executemany("INSERT IGNORE INTO dim_date (date_id, full_date, day, month, quarter, year, weekday) VALUES (%s,%s,%s,%s,%s,%s,%s)", inserts)
        conn.commit()
        print("[Loader] dim_date populated.")
    cur.close()
    # return date_lookup
    cur = conn.cursor()
    cur.execute("SELECT date_id, full_date FROM dim_date")
    rows = cur.fetchall()
    lookup = {}
    for r in rows:
        try:
            dobj = datetime.strptime(str(r[1]), "%Y-%m-%d").date()
        except:
            continue
        lookup[dobj] = int(r[0])
    cur.close()
    return lookup

# product lookup in memory
def load_product_lookup(csv_path=PRODUCT_CSV):
    print("[Loader] Loading product master into memory for fast lookup...")
    lookup = {}
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print("Product CSV not found:", csv_path)
        return {}
    for _, r in df.iterrows():
        pid = str(r['Product_ID'])
        price_raw = str(r.get('price$', '')).strip()
        if price_raw.startswith('$'):
            price_val = float(price_raw.replace('$', '').replace(',', '').strip())
        else:
            try:
                price_val = float(price_raw)
            except:
                price_val = 0.0
        lookup[pid] = {
            'product_id': pid,
            'product_category': r.get('Product_Category'),
            'price': price_val,
            'store_id': int(r['storeID']),
            'supplier_id': int(r['supplierID']),
            'store_name': r.get('storeName'),
            'supplier_name': r.get('supplierName')
        }
    print(f"[Loader] product lookup loaded ({len(lookup)} rows).")
    return lookup

# Stream reader thread (producer)
def stream_reader_thread(csv_path=TRANSACTIONAL_CSV, delay=STREAM_DELAY, loop_once=True):
    print("[Stream] Starting producer reading", csv_path)
    try:
        # Loop to simulate infinite stream if loop_once is False, 
        # or just read file once if loop_once is True.
        while True:
            for chunk in pd.read_csv(csv_path, chunksize=STREAM_CHUNK_SIZE):
                for _, r in chunk.iterrows():
                    # canonicalize keys and types
                    try:
                        row = {
                            'orderID': int(r['orderID']),
                            'Customer_ID': int(r['Customer_ID']),
                            'Product_ID': str(r['Product_ID']),
                            'quantity': int(r['quantity']),
                            'date': str(r['date'])
                        }
                    except Exception:
                        continue
                    
                    # block if buffer full
                    while True:
                        try:
                            stream_buffer.put(row, timeout=1)
                            break
                        except queue.Full:
                            time.sleep(0.05)
                    
                    if delay:
                        time.sleep(delay)
        
            if loop_once:
                break
                
        print("[Stream] Finished reading stream (producer).")
    except FileNotFoundError:
        print("[Stream] transactional CSV not found:", csv_path)
    except Exception as e:
        print("[Stream] ERROR while reading:", e)
        traceback.print_exc()
    finally:
        stream_finished.set()

# HybridJoin consumer
# HybridJoin consumer
def hybridjoin_consumer(db_conn, product_lookup, date_lookup):
    global available_slots, product_cache_last_refresh
    print("[Hybrid] Consumer started. HS=%s VP=%s" % (HASH_TABLE_SLOTS, DISK_BUFFER_SIZE))
    cur = db_conn.cursor()

    #reads file repeatedly
    def customer_partitions():
        while True:
            try:
                for chunk in pd.read_csv(CUSTOMER_CSV, chunksize=DISK_BUFFER_SIZE):
                    yield chunk
            except FileNotFoundError:
                print("[Hybrid] customer CSV not found:", CUSTOMER_CSV)
                return
            except Exception as e:
                print("[Hybrid] Error reading customer CSV:", e)
                traceback.print_exc()
                time.sleep(1)
                continue

    parts_iter = customer_partitions()

    inserts_buffer = []

    # main loop
    while True:
        # 1) Load up to w tuples
        with available_slots_lock:
            free = available_slots
        while free > 0 and not stream_buffer.empty():
            try:
                st = stream_buffer.get_nowait()
            except queue.Empty:
                break
            key = str(int(st['Customer_ID']))  # canonical string key
            node = DLLNode(key)
            node.timestamp = time.time()
            entry = {
                'stream': st,
                'node': node,
                'ts': time.time()
            }
            with hash_lock:
                hash_table[key].append(entry)
            stream_queue.append(node)
            with available_slots_lock:
                available_slots -= 1
                free = available_slots

        # termination condition
        if stream_finished.is_set() and stream_buffer.empty() and len(hash_table) == 0 and len(stream_queue) == 0:
            print("[Hybrid] Stream finished and processing complete.")
            break

        # 2) get next partition from customer master
        try:
            disk_df = next(parts_iter)
        except StopIteration:
            # no partitions available -> small sleep
            time.sleep(0.1)
            continue
        except Exception as e:
            time.sleep(0.1)
            continue

        # 3) probe each customer in disk buffer
        for _, crow in disk_df.iterrows():
            try:
                cust_key = str(int(crow['Customer_ID']))
            except Exception:
                continue
            with hash_lock:
                bucket = hash_table.get(cust_key)
                if not bucket:
                    continue
                # copy matched entries
                matched = list(bucket)
                # remove bucket
                hash_table.pop(cust_key, None)

            # process matched stream entries
            for ent in matched:
                st = ent['stream']
                node = ent['node']

                # transform: product lookup
                product_id = str(st['Product_ID'])
                prod = product_lookup.get(product_id)
                if prod is None:
                    # missing product -> skip, could log
                    continue

                # transform: date -> date_id
                try:
                    dobj = datetime.strptime(st['date'], "%Y-%m-%d").date()
                except Exception:
                    # try pandas parse
                    try:
                        dobj = pd.to_datetime(st['date']).date()
                    except:
                        continue
                date_id = date_lookup.get(dobj)
                if date_id is None:
                    # date not in dim_date; skip
                    continue

                # compute revenue
                qty = int(st['quantity'])
                price = float(prod['price'])
                revenue = price * qty

                # prepare fact row
                # Note: We still use store_id/supplier_id here for the FACT table, which is correct.
                fact_row = (
                    int(st['orderID']),
                    product_id,
                    int(st['Customer_ID']),
                    int(date_id),
                    int(prod['store_id']),
                    int(prod['supplier_id']),
                    qty,
                    float(revenue)
                )
                inserts_buffer.append(fact_row)

                # ensure dims for product/store/supplier and customer exist in database
                try:
                    # dim_customer (from crow)
                    cust_row = (
                        int(crow['Customer_ID']),
                        crow.get('Gender'),
                        str(crow.get('Age')),
                        crow.get('Occupation'),
                        crow.get('City_Category'),
                        str(crow.get('Stay_In_Current_City_Years')),
                        1 if int(crow.get('Marital_Status', 0)) else 0
                    )
                    cur.execute("INSERT IGNORE INTO dim_customer (customer_id, gender, age, occupation, city_category, stay_in_current_city_years, marital_status) VALUES (%s,%s,%s,%s,%s,%s,%s)", cust_row)
                    
                    # store
                    cur.execute("INSERT IGNORE INTO dim_store (store_id, store_name) VALUES (%s,%s)",
                                (prod['store_id'], prod['store_name']))
                    
                    # supplier
                    cur.execute("INSERT IGNORE INTO dim_supplier (supplier_id, supplier_name) VALUES (%s,%s)",
                                (prod['supplier_id'], prod['supplier_name']))
                    
                    # product -- UPDATED: Removed store_id and supplier_id from this INSERT
                    cur.execute("INSERT IGNORE INTO dim_product (product_id, product_category, price) VALUES (%s,%s,%s)",
                                (prod['product_id'], prod['product_category'], prod['price']))
                    
                    # commit per partition inserts lightly (not per-row)
                    conn_commit = False
                except Exception as e:
                    # ignore dim insert errors but log
                    print("[Hybrid] DIM insert error:", e)
                    conn_commit = False

                # remove node from queue (random deletion)
                try:
                    stream_queue.remove(node)
                except Exception:
                    pass

                # free up a slot
                with available_slots_lock:
                    available_slots += 1

            # after processing matched bucket, periodically flush inserts_buffer to DB
            if len(inserts_buffer) >= BATCH_INSERT_SIZE:
                try:
                    cur.executemany(
                        "INSERT IGNORE INTO fact_sales (order_id, product_id, customer_id, date_id, store_id, supplier_id, quantity, revenue) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        inserts_buffer
                    )
                    db_conn.commit()
                except Exception as e:
                    print("[Hybrid] Error inserting batch:", e)
                    db_conn.rollback()
                inserts_buffer = []

        # small sleep to avoid 100% CPU
        time.sleep(0.01)

        # TTL eviction to avoid unbounded growth (evict entries older than TTL)
        nowt = time.time()
        if stream_queue.head and (nowt - stream_queue.head.timestamp) > ENTRY_TTL_SECONDS:
            # evict oldest node(s)
            node_old = stream_queue.peek_oldest()
            while node_old and (time.time() - node_old.timestamp) > ENTRY_TTL_SECONDS:
                # remove bucket entries referencing this key
                k = node_old.key
                with hash_lock:
                    b = hash_table.pop(k, [])
                    # decrease available slots accordingly
                    with available_slots_lock:
                        available_slots += len(b)
                stream_queue.remove(node_old)
                node_old = stream_queue.peek_oldest()
                # continue

    # final flush
    if inserts_buffer:
        try:
            cur.executemany(
                "INSERT IGNORE INTO fact_sales (order_id, product_id, customer_id, date_id, store_id, supplier_id, quantity, revenue) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                inserts_buffer
            )
            db_conn.commit()
        except Exception as e:
            print("[Hybrid] Final insert error:", e)
            db_conn.rollback()

    cur.close()
    print("[Hybrid] Consumer finished.")

# Runner: integrate loaders and hybrid join
def main():
    global db_conn
    db_conn = connect_db_prompt()
    if not db_conn:
        print("Cannot proceed without DB connection.")
        return

    # 1) Pre-load DIMs (customers, products, dates)
    # You can skip reloading dim_customer/dim_product if already loaded.
    load_product_dim(db_conn, PRODUCT_CSV)
    load_customer_dim(db_conn, CUSTOMER_CSV)
    date_lookup = populate_dim_date(db_conn)

    # 2) Load product lookup into memory
    product_lookup = load_product_lookup(PRODUCT_CSV)

    # 3) Start stream thread and hybrid consumer thread
    producer = threading.Thread(target=stream_reader_thread, args=(TRANSACTIONAL_CSV, STREAM_DELAY, True), daemon=True)
    consumer = threading.Thread(target=hybridjoin_consumer, args=(db_conn, product_lookup, date_lookup), daemon=False)

    print("[Run] Starting ETL: producer + hybrid consumer")
    t0 = time.time()
    producer.start()
    consumer.start()

    consumer.join()  # wait until consumer finishes processing
    t1 = time.time()
    print("[Run] ETL finished in %.2f seconds." % (t1 - t0))

    if db_conn.is_connected():
        db_conn.close()
        print("DB connection closed.")

if __name__ == "__main__":
    main()
