from elasticsearch import Elasticsearch
import srt 
import os
import json

import logging

logging.basicConfig(level=logging.INFO)

class StorageKeeper:

    def __init__(self, host="localhost", port=9200):
        self.es = Elasticsearch([{"host": host, "port": port}])
    
    def push_subs(self, file, idx="khan_academy"):
        """ Works with modified .srt files.
            Creates a document for EVERY LINE in the subtitles.

            The 0's entry contains metadata.
            0
            00:00:00,000 --> 00:00:00,000
            {"url":"url", "name":"name"}
        """
        body = {}
        with open(file, 'r') as f:
            srt_lines = srt.parse(f.read())
        meta_data = json.loads(next(srt_lines).content)
        body['url'] = meta_data['url']
        body['name'] = meta_data['name']
        for line in srt_lines:
            body['time'] = int(line.start.total_seconds())
            body['content'] = line.content
            logging.debug(str(idx))
            print(self.es.index(index=idx, doc_type='_doc', body = body))
    
    def search_subs(self, search_phrase, idx="khan_academy"):
        """ Searches for the given search_phrase in the given index (full-text SEARCH).
            Returns top-n matches.
        """        
        body = {"query": 
                {
                    "match": 
                    {
                        "content":
                        {
                            "query": f"{search_phrase}", 
                            "fuzziness": 1
                        } 
                    }
                }
               }

        res = self.es.search(index=idx, doc_type="_doc", body=body)
        
        logging.debug(str(res))

        hits = []

        for r in res['hits']['hits']:
            vid_name = r['_source']['name']
            snippet_text = r['_source']['content']
            # snippet_url = 'https://www.youtube.com/embed/'+r['_source']['url'][8:]+'?start='+str(r['_source']['time'])
            snippet_url = r['_source']['url'][8:]
            start_time = str(r['_source']['time'])
            hits.append((vid_name, snippet_text, snippet_url, start_time))
        
        return hits

def create_index():

    es = Elasticsearch()

    mappings = {"_doc":
                {
                "properties":
                {
                "url": {"type": "text"},
                "name": {"type": "text"},
                "time": {"type": "short"},
                "content": {"type": "text"}
                }
                }
            }

    if es.indices.exists("khan_academy"):
        es.indices.delete("khan_academy")
    
    es.indices.create("khan_academy", {"mappings": mappings})