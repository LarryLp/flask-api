#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import requests
from flask import Flask, request, json
from flask_apscheduler import APScheduler
import yaml

from utils import Constant


class Config(object):
    JOBS = [
        {
            'id': 'process_task_queue',
            'func': '__main__:process_task_queue',
            # 'args': (1, 2),
            'trigger': 'interval',
            'seconds': 5,
        },
        # {
        #     'id': 'check_task_status',
        #     'func': '__main__:check_task_status',
        #     # 'args': (1, 2),
        #     'trigger': 'interval',
        #     'seconds': 5,
        # }
    ]


def process_task_queue():
    # 0队列检查
    # pending_task = Constant.get_pending_tasks()
    pending_task = False
    if pending_task:
        # 1资源检查
        resouces = []
        task_id = resouces[0]['_id']  # 每次处理一个task
        if resouces:
            try:
                depolyed = False
                # 2.1创建任务容器
                pass
                # 2.2更新task状态:创建中
                Constant.update_task_status(task_id, -1)

                # 3.1 检查容器状态
                if depolyed:
                    # 3.2更新task状态:检测中
                    Constant.update_task_status(task_id, 0)
            except Exception as e:
                # 更新task状态: error
                Constant.update_task_status(task_id, -3)



app = Flask(__name__)
app.config.from_object(Config())


# REST APIs of user
@app.route('/api/v1/user/login', methods=['POST'])
def login():
    result = {"code": 400, "message": "service is unavailable!", "data": {}}
    if request.method == 'POST':
        try:
            token = ''
            body = json.loads(request.get_data(as_text=True))
            userName = body['userName']
            password_md5 = Constant.getMD5(body['password'])

            url = Constant.baseUrl + 'user/_search'
            header = {"Content-Type": "application/json; charset=UTF-8"}
            data = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "match": {
                                    "username": userName
                                }
                            },
                            {
                                "match": {
                                    "password": password_md5
                                }
                            }
                        ]
                    }
                }
            }
            reponse = requests.post(url=url, data=json.dumps(data), headers=header)
            reponse_dict = json.loads(reponse.text)
            if reponse_dict["hits"]["hits"]:
                userId = reponse_dict["hits"]["hits"][0]["_id"]
                create = Constant.create_token(userId)
                if create[0]:
                    token = create[1]['access_token']
        except Exception as e:
            result["message"] = e
        else:
            if token:
                result["code"] = 200
                result["message"] = "validated"
                result["data"].update({'token': token})
            else:
                result["message"] = "用户名或密码错误"
    else:
        result["message"] = "Invalid Request Method!"
    return result


@app.route('/api/v1/user/get_info', methods=['POST'])
def get_info():
    result = {"code": 400, "message": "service is unavailable!", "data": ""}
    if request.method == 'POST':
        try:
            body = json.loads(request.get_data(as_text=True))
            token = body['token']
            verify = Constant.verify_token(token)
            userId = verify[1]['userId']

            url = Constant.baseUrl + 'user/_search'
            header = {"Content-Type": "application/json; charset=UTF-8"}
            query = {
                "query": {
                    "bool": {
                        "must":
                            {
                                "match": {
                                    "_id": userId
                                }
                            }
                    }
                }
            }
            reponse = requests.post(url=url, data=json.dumps(query), headers=header)
            reponse_dict = json.loads(reponse.text)

            source = reponse_dict["hits"]["hits"][0]['_source']
            data = {'avatar': source['avator'], 'access': source['access'], 'userName': source['username'],
                    'userId': userId}
        except Exception as e:
            print(e)
            result["message"] = e
        else:
            if source:
                result["code"] = 200
                result["message"] = "success"
                result['data'] = data
            else:
                result["message"] = "无法获取用户信息"
    else:
        result["message"] = "Invalid Request Method!"
    return result


# REST APIs of cloud-platform
@app.route('/api/v1/platform/add', methods=['POST'])
def addPlatform():
    result = {"code": 400, "message": "service is unavailable!", "token": ""}
    if request.method == 'POST':
        try:
            body = json.loads(request.get_data(as_text=True))
            body['join_field'] = {'name': 'platform'}

            url = Constant.baseUrl + 'platform-task/_doc'
            header = {"Content-Type": "application/json; charset=UTF-8"}
            reponse = requests.post(url=url, data=json.dumps(body), headers=header)
            reponse_dict = json.loads(reponse.text)
        except Exception as e:
            print(e)
            result["message"] = e
        else:
            if reponse_dict["result"] == "created":
                result["code"] = 200
                result["message"] = "success"
            else:
                result["message"] = reponse
    else:
        result["message"] = "Invalid Request Method!"
    return result


@app.route('/api/v1/platform/search', methods=['GET'])
def queryPlatform():
    result = {"code": 400, "message": "service is unavailable!", "data": []}
    if request.method == 'GET':
        try:
            query = request.args.to_dict()
            data = {
                "size": 2000,
                "query": {
                    "bool": {
                        "must": []
                    }
                },
                "sort": {
                    "createdTime": {
                        "order": "desc"
                    }
                }
            }
            filter = [{"term": {"join_field": "platform"}}]
            if list(query.keys()):
                key = list(query.keys())[0]
                if key == 'owner':
                    filter.append({"wildcard": {"owner.keyword": "*%s*" % query[key]}})
                if key == 'name':
                    filter.append({"wildcard": {"name.keyword": "*%s*" % query[key]}})
            data['query']['bool']['must'] = filter

            # url = Constant.baseUrl + 'platform-task/_search?_source_includes=name,owner,rate,createdTime,detectedTime'
            url = Constant.baseUrl + 'platform-task/_search'
            header = {"Content-Type": "application/json; charset=UTF-8"}
            reponse = requests.post(url=url, data=json.dumps(data), headers=header)
            reponse_dict = json.loads(reponse.text)

        except Exception as e:
            print(e)
            result["message"] = e
        else:
            originalData = reponse_dict['hits']['hits']
            if originalData:
                filterData = []
                for each in originalData:
                    tmp = {}
                    tmp.update(each['_source'])
                    tmp.update({'taskId': each['_id']})
                    # 格式化datetime
                    if tmp['createdTime'] <= 0:
                        tmp.update({'createdTime': ''})
                    else:
                        tmp.update({'createdTime': Constant.formatDateTime(tmp['createdTime'])})
                    if tmp['detectedTime'] <= 0:
                        tmp.update({'detectedTime': ''})
                    else:
                        tmp.update({'detectedTime': Constant.formatDateTime(tmp['detectedTime'])})
                    filterData.append(tmp)
                result['data'] = filterData
                result["code"] = 200
                result["message"] = "success"
            else:
                result["code"] = 200
                result["message"] = "success"
    else:
        result["message"] = "Invalid Request Method!"
    return result


# REST APIs of tasks
@app.route('/api/v1/task/add', methods=['POST'])
def add():
    result = {"code": 400, "message": "service is unavailable!", "data": ""}
    if request.method == 'POST':
        try:
            body = json.loads(request.get_data(as_text=True))
            parentDocId = body['parentDocId']

            url = Constant.baseUrl + 'platform-task/_doc/?routing=%s&refresh' % parentDocId
            header = {"Content-Type": "application/json; charset=UTF-8"}
            data = {
                "taskName": body['taskName'],
                "taskDescription": body['taskDescription'],
                "testedComponents": body['testedComponents'],
                "status":
                    {
                        "startTime": "2019-12-30 08:30:34",
                        "sendTime": "2019-12-30 11:30:54",
                        "percentage": 0.87,
                        "total": 10,
                        "success": 10,
                        "process": 10,
                        "pending": 10,
                        "error": 2
                    },
                "join_field": {"name": "task", "parent": parentDocId}
            }
            reponse = requests.post(url=url, data=json.dumps(data), headers=header)
            reponse_dict = json.loads(reponse.text)
        except Exception as e:
            print(e)
            result["message"] = e
        else:
            if reponse_dict["result"] == "created":
                result["code"] = 200
                result["message"] = "success"
            else:
                result["message"] = reponse
    else:
        result["message"] = "Invalid Request Method!"
    return result


@app.route('/api/v1/task/delete', methods=['DELETE'])
def delete():
    result = {"code": 400, "message": "service is unavailable!", "data": ""}
    if request.method == 'DELETE':
        try:
            docId = request.args.to_dict()['taskId']
            url = Constant.baseUrl + 'platform-task/_doc/%s' % docId

            reponse = requests.delete(url=url)
            reponse_dict = json.loads(reponse.text)
        except Exception as e:
            print(e)
            result["message"] = e
        else:
            if reponse_dict["result"] == "deleted":
                result["code"] = 200
                result["message"] = "success"
            else:
                result["message"] = reponse
    else:
        result["message"] = "Invalid Request Method!"
    return result


@app.route('/api/v1/task/search', methods=['POST'])
def search():
    """
    :param name: 云平台名称
    :param owner: 云平台所有者
    :param taskName: 任务名称
    :param startTime: 时间条件开始值
    :param endTime: 时间条件结束值
    :param percentage: 任务执行状态
    :return list:list类型中每个元素为平台信息+对应的任务信息
    """
    result = {"code": 400, "message": "service is unavailable!", "data": ""}
    if request.method == 'POST':
        try:
            body = json.loads(request.get_data(as_text=True))
            # 平台信息的查询条件处理
            if 'name' in body.keys() or 'owner' in body.keys():
                hits = Constant.searchPlatform(body)
                # 没有查询到就没有必要继续查了
                if hits:
                    if 'taskName' in body.keys() or 'startTime' in body.keys() or 'endTime' in body.keys() or 'status' in body.keys():
                        # 平台+任务查询条件
                        hit = Constant.searchTask(body, hits)
                        result["code"] = 200
                        result["data"] = Constant.getData(hit)
                        result["message"] = "success"
                    else:
                        # 仅平台查询条件
                        hit = Constant.searchTask(body, hits)
                        result["code"] = 200
                        result["data"] = Constant.getData(hit)
                        result["message"] = "success"
                else:
                    # 平台查询条件未命中，则不需在执行查询了
                    result["code"] = 200
                    result["data"] = hits
                    result["message"] = "success"
            elif 'taskName' in body.keys() or 'startTime' in body.keys() or 'endTime' in body.keys() or 'status' in body.keys():
                # 仅任务查询条件
                hit = Constant.searchTask(body, [])
                result["code"] = 200
                result["data"] = Constant.getData(hit)
                result["message"] = "success"
            else:
                # 返回全部
                hit = Constant.searchTask(body, [])
                result["code"] = 200
                result["data"] = Constant.getData(hit)
                result["message"] = "success"

        except Exception as e:
            print(e)
            result["message"] = e
    else:
        result["message"] = "Invalid Request Method!"
    return result


@app.route('/api/v1/task/status', methods=['GET'])
def getStatus():
    result = {"code": 400, "message": "service is unavailable!", "data": ""}
    if request.method == 'GET':
        try:
            taskId = request.args.to_dict()['taskId']
            url = Constant.baseUrl + 'platform-task/_doc/%s?_source_includes=status' % taskId
            reponse = requests.get(url=url)
            reponse_dict = json.loads(reponse.text)
            if reponse_dict["found"]:
                status = reponse_dict['_source']['status']
                status['startTime'] = Constant.formatDateTime(status['startTime'])
                status['endTime'] = Constant.formatDateTime(status['endTime'])
        except Exception as e:
            print(e)
            result["message"] = e
        else:
            if status:
                result["code"] = 200
                result["data"] = status
                result["message"] = "success"
            else:
                result["message"] = reponse
    else:
        result["message"] = "Invalid Request Method!"
    return result


@app.route('/api/v1/task/components', methods=['GET'])
def getComponents():
    result = {"code": 400, "message": "service is unavailable!", "data": ""}
    if request.method == 'GET':
        try:
            taskId = request.args.to_dict()['taskId']
            url = Constant.baseUrl + 'taskdetail/_search'
            header = {"Content-Type": "application/json; charset=UTF-8"}
            data = {
                "size": 0,
                "query": {
                    "term": {
                        "taskId.keyword": {
                            "value": taskId,
                            "boost": 1
                        }
                    }
                },
                "aggs": {
                    "taskName": {
                        "terms": {
                            "field": "taskId.keyword"
                        },
                        "aggs": {
                            "taskName": {
                                "terms": {
                                    "field": "taskName.keyword"
                                },
                                "aggs": {
                                    "componentType": {
                                        "terms": {
                                            "field": "type.keyword"
                                        },
                                        "aggs": {
                                            "componentName": {
                                                "terms": {
                                                    "field": "componentName.keyword"
                                                },
                                                "aggs": {
                                                    "startTime": {
                                                        "min": {
                                                            "field": "startTime"
                                                        }
                                                    },
                                                    "endTime": {
                                                        "max": {
                                                            "field": "endTime"
                                                        }
                                                    },
                                                    "status": {
                                                        "terms": {
                                                            "field": "status"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            reponse = requests.post(url=url, data=json.dumps(data), headers=header)
            reponse_dict = json.loads(reponse.text)
            data = Constant.formatComponents(reponse_dict)
        except Exception as e:
            print(e)
            result["message"] = e
        else:
            result["code"] = 200
            result["data"] = data
            result["message"] = "success"
    else:
        result["message"] = "Invalid Request Method!"
    return result


@app.route('/api/v1/task/components/interfaces', methods=['GET'])
def getInterfaces():
    result = {"code": 400, "message": "service is unavailable!", "data": ""}
    if request.method == 'GET':
        try:
            taskId = request.args.to_dict()['taskId']
            componentName = request.args.to_dict()['componentName']
            url = Constant.baseUrl + 'taskdetail/_search'
            header = {"Content-Type": "application/json; charset=UTF-8"}
            data = {
                "_source": ["interfaceName", "startTime", "endTime", "status", "result"],
                "query": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "taskId.keyword": taskId
                                }
                            },
                            {
                                "term": {
                                    "componentName.keyword": componentName
                                }
                            }
                        ]
                    }
                }
            }

            reponse = requests.post(url=url, data=json.dumps(data), headers=header)
            reponse_dict = json.loads(reponse.text)
            hits = reponse_dict['hits']['hits']
            if hits:
                hits = [each['_source'] for each in hits]

        except Exception as e:
            print(e)
            result["message"] = e
        else:
            result["code"] = 200
            result["data"] = hits
            result["message"] = "success"
    else:
        result["message"] = "Invalid Request Method!"
    return result


# REST APIs of interface parameters
@app.route('/api/v1/parameters/search', methods=['GET'])
def get_parameters():
    result = {"code": 400, "message": "service is unavailable!", "data": []}
    if request.method == 'GET':
        try:
            url = Constant.baseUrl + 'parameters/_search'
            componentName = request.args.to_dict()['componentName']
            header = {"Content-Type": "application/json; charset=UTF-8"}
            data = {
              "_source": ["interfaceName", "url", "httpVerb", "query", "response"],
              "query": {
                "bool": {
                  "must": [
                    {
                      "term": {
                        "componentName.keyword": componentName
                      }
                    }
                  ]
                }
              }
            }

            reponse = requests.post(url=url, data=json.dumps(data), headers=header)
            reponse_dict = json.loads(reponse.text)
            hits = reponse_dict['hits']['hits']
        except Exception as e:
            print(e)
            result["message"] = e
        else:
            if hits:
                result["code"] = 200
                result["data"] = Constant.format_parameters(hits)
                result["message"] = "success"
            else:
                result["code"] = 200
                result["data"] = hits
                result["message"] = "success"
    else:
        result["message"] = "Invalid Request Method!"
    return result


# REST APIs of K8S-task
@app.route('/api/v1/k8s-task/add', methods=['GET'])
def create_k8s_task():
    result = {"code": 400, "message": "service is unavailable!", "data": []}
    if request.method == 'GET':
        try:
            component_list = request.args.to_dict()['component_list'].split(' ')

            # default: task_yaml['command'] = ['python3', './main.py', 'ALL']
            task_file = open('./task-pod.yaml')
            task_yaml = yaml.load(task_file, Loader=yaml.FullLoader)

            # base_command
            base_command = task_yaml['spec']['containers'][0]['command'][:-1]

            # generate new command
            command = base_command + component_list
            task_yaml['spec']['containers'][0]['command'] = command

            # request for creating k8s pod
            yYaml = yaml.dump(task_yaml)
            url = 'https://172.18.103.72:6443/api/v1/namespaces/default/pods'

            token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6Ik16UHQyQThPME5Hb1RhU3E0cjVlR2QtMUtuTGt0U1BqVGF2VXk3SE1ENEEifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImRlZmF1bHQtdG9rZW4tODR2NzUiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiZGVmYXVsdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjkwMDJmMzBjLTg1NWQtNDUyYy05MzcwLTc5N2E1YmU4OWU4YSIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDpkZWZhdWx0OmRlZmF1bHQifQ.pfDRGFacQcHTt6Y601pt-PNek0QqawwFN1m1RGz8pxhRsvI_Ur5SUe5KVqgFCEDoOpQWjDzUGOxQshIX3svXzKQ_v1yQWIwYpOWNX-LmR-lwU96FOfbGHGA1sTRWuGU58o77CIq5EmFbPSHUqQprsUbNrMi1H0VagfkeDcZjua_ZPdTkaoc8sdOvynYtOovni_HiUN7D-TDzdHHR8iJGRDKPBf8URDvoywwDyzqCLD_XzR72YkF1oCel9U-8Rqrp_B92BGRauYpO3wAFbu0xHmueEmUc8yQaGXbz1rhezGczoDVIdj6MjNQ_7_ueaU2Gj2m11L1hcLDRFIWdxlub3Q'
            head = {'Content-Type': 'application/yaml', 'Authorization': 'Bearer ' + token}

            r = requests.post(url, headers=head, data=task_yaml, verify=False)
            print(r.text)
        except Exception as e:
            result["message"] = e
        else:
            result["code"] = 200
            result["data"] = task_yaml
            result["message"] = "success"
    else:
        result["message"] = "Invalid Request Method!"
    return result


if __name__ == "__main__":
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    app.run(host='0.0.0.0', debug=True)
