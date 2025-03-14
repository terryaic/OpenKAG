
from db import user_kdb_mgdb
from advancerag import AdvancedRAG
import os
import threading
import time

class KDBManager():
    def __init__(self):
        self.kdb_pool = {}

    async def create_or_get_rag(self, kdb_id, prompt=None):
        if kdb_id not in self.kdb_pool.keys():
            print("init kdb id:%s"%kdb_id)
            rpath = user_kdb_mgdb.get_address(kdb_id=kdb_id)['address']
            #dbpath = os.path.join(rpath, "milvus.db")
            dbpath = None
            fpath = os.path.join(rpath,"res_files")
            storage_dir = os.path.join(rpath,"storage")
            adrag = AdvancedRAG()
            await adrag.init(dbpath, fpath, storage_dir, prompt=prompt)
            self.kdb_pool[kdb_id] = adrag
        else:
            adrag = self.kdb_pool[kdb_id]
        return adrag
    
    def release_rag(self, kdb_id):
        if kdb_id in self.kdb_pool.keys():
            print("release kdb:", kdb_id)
            adrag = self.kdb_pool[kdb_id]
            adrag.close()
            return True
        return False
    
kdbm = KDBManager()
def kdbm_monitor(expired_time):
    while True:
        kdb_ids = []
        for item in kdbm.kdb_pool.items():
            if item[1].last_active_time + expired_time < time.time():
                if kdbm.release_rag(item[0]):
                    kdb_ids.append(item[0])
        for kdb_id in kdb_ids:
            kdbm.kdb_pool.pop(kdb_id)
        import gc
        gc.collect()
        import torch
        torch.cuda.empty_cache()
        time.sleep(10)

def start_kdbm_monitor(expired_time):
    if expired_time > 0:
        kdbm_thread = threading.Thread(target=kdbm_monitor, args=(expired_time,))
        kdbm_thread.start()
