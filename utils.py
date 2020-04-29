#!/usr/bin/python
# -*- coding: UTF-8 -*-

import hashlib
import jwt
import time
import requests
from flask import json

class Constant:

    baseUrl = 'http://172.18.103.73:9200/'
    authorization = True

    @classmethod
    def searchTask(cls, body, hits):
        url = cls.baseUrl + 'platform-task/_search?_source_includes=name,owner'
        header = {"Content-Type": "application/json; charset=UTF-8"}
        data = {
            "size": 2000,
            "query": {
                "has_child": {
                    "type": "task",
                    "query": {
                        "bool": {
                            "must": []
                        }
                    },
                    "inner_hits": {
                        "size": 100
                    }
                }
            }
        }
        timeRange = {"range": {"status.startTime": {}}}
        if 'taskName' in body.keys():
            value = "*%s*" % body['taskName']
            data['query']['has_child']['query']['bool']['must'].append({"wildcard": {"taskName.keyword": value}})

        if 'startTime' in body.keys():
            timeRange['range']["status.startTime"].update({"gte": body['startTime']})
        if 'endTime' in body.keys():
            timeRange['range']["status.startTime"].update({"lte": body['endTime']})
        if timeRange['range']["status.startTime"]:
            data['query']['has_child']['query']['bool']['must'].append(timeRange)

        if 'status' in body.keys() and body['status'] != '全部':
            value = {'未启动': {"lt": 0}, '进行中': {"gte": 0, "lt": 1}, '已完成': {"eq": 1}, '失败': {"gt": 1}}
            data['query']['has_child']['query']['bool']['must'].append(
                {"range": {"status.percentage": value[body['status']]}})
        if hits:
            taskId = [each["_id"] for each in hits]
            data['query']['has_child']['query']['bool']['must'].append({"terms": {"_id": taskId}})
        print('task ', data)
        reponse = requests.post(url=url, data=json.dumps(data), headers=header)
        reponse_dict = json.loads(reponse.text)
        hit = reponse_dict["hits"]["hits"]
        return hit

    @classmethod
    def searchPlatform(cls, body):
        url = cls.baseUrl + 'platform-task/_search?_source_includes=_id'
        header = {"Content-Type": "application/json; charset=UTF-8"}
        data = {
            "size": 2000,
            "query": {
                "has_parent": {
                    "parent_type": "platform",
                    "query": {
                        "bool": {
                            "must": []
                        }
                    }
                }
            }
        }
        if 'name' in body.keys():
            value = "*%s*" % body['name']
            data['query']['has_parent']['query']['bool']['must'].append({"wildcard": {"name.keyword": value}})
        if 'owner' in body.keys():
            value = "*%s*" % body['owner']
            data['query']['has_parent']['query']['bool']['must'].append({"wildcard": {"owner.keyword": value}})
        print('platform ', data)
        reponse = requests.post(url=url, data=json.dumps(data), headers=header)
        reponse_dict = json.loads(reponse.text)
        hits = reponse_dict["hits"]["hits"]
        return hits

    @classmethod
    def getData(cls, data_list):
        result = []
        if data_list:
            for each in data_list:
                for inner in each['inner_hits']['task']['hits']['hits']:
                    tmp = {'name': each['_source']['name'], 'owner': each['_source']['owner']}

                    tmp['taskId'] = inner['_id']
                    tmp['taskName'] = inner['_source']['taskName']
                    tmp['startTime'] = cls.formatDateTime(inner['_source']['status']['startTime'])
                    tmp['endTime'] = cls.formatDateTime(inner['_source']['status']['endTime'])
                    tmp['status'] = inner['_source']['status']['percentage']
                    result.append(tmp)
        return result

    @classmethod
    def formatDateTime(cls, timeStamp):
        timeArray = time.localtime(timeStamp)
        formatTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        return formatTime

    @classmethod
    def formatComponents(cls, data_dict):
        result = []
        # it must have only one record
        buckets = data_dict['aggregations']['taskName']['buckets'][0]
        if buckets:
            for each in buckets['taskName']['buckets'][0]['componentType']['buckets']:
                for item in each['componentName']['buckets']:
                    tmp = {'taskId': buckets['key'], 'taskName': buckets['taskName']['buckets'][0]['key']}
                    tmp['componentType'] = each['key']
                    tmp['componentName'] = item['key']
                    tmp['startTime'] = cls.formatDateTime(item['startTime']['value'])
                    tmp['endTime'] = cls.formatDateTime(item['endTime']['value'])

                    done = 0
                    for each_json in item['status']['buckets']:
                        if each_json['key'] == 1:
                            done = each_json['doc_count']
                            break
                    tmp['status'] = round(done / item['doc_count'], 2) * 100

                    result.append(tmp)
        return result

    @classmethod
    def get_pending_tasks(cls):
        url = cls.baseUrl + 'platform-task/_search?_source_includes=_id'
        header = {"Content-Type": "application/json; charset=UTF-8"}
        data = {
          "size": 2000,
          "query": {
            "bool": {
              "must": [
                {
                  "term": {
                    "status": -2
                  }
                },
                {
                  "term": {
                    "join_field": "task"
                  }
                }
              ]
            }
          },
          "sort": {
            "createdTime": {
              "order": "asc"
            }
          }
        }
        reponse = requests.post(url=url, data=json.dumps(data), headers=header)
        reponse_dict = json.loads(reponse.text)
        hits = reponse_dict["hits"]["hits"]
        return hits

    @classmethod
    def update_task_status(cls, task_id, status_value):
        url = cls.baseUrl + '/platform-task/_update/' + task_id
        header = {"Content-Type": "application/json; charset=UTF-8"}
        data = {
          "doc": {
            "status": status_value
          }
        }
        reponse = requests.post(url=url, data=json.dumps(data), headers=header)
        reponse_dict = json.loads(reponse.text)
        updated = reponse_dict["result"]
        return updated

    @classmethod
    def format_parameters(cls, result_list):
        result_dict = {}
        for each in result_list:
            each = each['_source']
            result_dict.update({each['interfaceName']: {'url': each['url'], 'httpVerb':each['httpVerb'], 'query': each['query'], 'response': each['response']}})
        return result_dict

    @classmethod
    def getMD5(cls, str):
        password_str = str.encode(encoding='utf-8')
        md5 = hashlib.md5()
        md5.update(password_str)
        return md5.hexdigest()

    @classmethod
    def create_token(cls, userId):
        # payload
        payload = {
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "userId": userId
        }

        # headers
        headers = {'alg': "HS256"}

        # jwt token
        token = jwt.encode(payload, "kuochin1989", algorithm="HS256", headers=headers).decode('ascii')
        return True, {'access_token': token, 'userId': userId}

    @classmethod
    def verify_token(cls, token):
        try:
            payload = jwt.decode(token, 'kuochin1989', algorithms=['HS256'])
        except Exception as e:
            print(e)
            return False, token
        else:
            return True, {'access_token': token, 'userId': payload['userId']}
