import bminf
import json
import pickle
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
import WebApp.server.params as params
from demo.call import prompt_with_json, coref_with_json, dict_with_json
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s')  #
# logging.disable(logging.INFO)
define("port", default=5314, help="run on the given port", type=int)
# request types
TYPE_ERROR = -1
TYPE_GET_PROMPT_ALIAS = 0
TYPE_GET_COREF_ALIAS = 1
TYPE_GET_DICT_ALIAS = 2

# m_infoManager = InfoManager()

# load model
# chinese_model = bminf.models.CPM2(device=params.gpu_id)
# load coref result
logging.info("start reading")
bd_id2coref_alias = json.load(open('/data/tsq/xlink/coref/bd/coref_stanford_parse_all_abstract.json', 'r'))
wiki_id2coref_alias = json.load(open('/data/tsq/xlink/coref/wiki/coref_stanford_parse_all_abstract.json', 'r'))
bd_mention2ids = pickle.load(open('/data/tsq/xlink/bd/mention2ids.pkl', 'rb'))
wiki_mention2ids = pickle.load(open('/data/tsq/xlink/wiki/mention2ids.pkl', 'rb'))
bd_id2mention = pickle.load(open('/data/tsq/xlink/bd/id2mention.pkl', 'rb'))
wiki_id2mention = pickle.load(open('/data/tsq/xlink/wiki/id2mention.pkl', 'rb'))
logging.info("finish reading")


class PostHandler(tornado.web.RequestHandler):
    def options(self):
        # no body
        logging.debug('Received OPTIONS request')
        self.set_status(204)

    def post(self):
        # Protocol implemented here based on the client messages.
        try:
            # load the json received from the client:
            clientJson = json.loads(self.request.body.decode('utf-8'))
            logging.info('Got JSON data: ' + str(clientJson))
            requestType, clientId = self.getRequestTypeFromClientJson(clientJson)
            logging.info('Got requestType: ' + str(requestType))
            # DEBUG:
            # returnJson = {"haha": "xi"}
            # self.write(returnJson)  # send JSON to client
            # logging.info('Sending JSON data: ' + str(returnJson))
            # self.render('result.html')
            # logging.info("parsed result.html")
            # self.write()
            # if client sent an unknown json:
            if requestType == TYPE_ERROR:
                returnJson = self.getErrorJson('Undefined JSON received.')
            else:
                # m_infoManager.createClient(clientId)
                if requestType == TYPE_GET_PROMPT_ALIAS:
                    returnJson = self.getPromptAliasJson(clientJson)
                elif requestType == TYPE_GET_COREF_ALIAS:
                    returnJson = self.getCorefAliasJson(clientJson)
                elif requestType == TYPE_GET_DICT_ALIAS:
                    returnJson = self.getDictAliasJson(clientJson)
                else:
                    returnJson = self.getErrorJson('Undefined requestType received.')

        except Exception as e:
            logging.error('Caught error from unknown location: ' + str(e))
            returnJson = self.getErrorJson('Please try again. General error: ' + str(e))

        logging.info('Sending JSON data: ' + str(returnJson))
        self.write(json.dumps(returnJson))  # send JSON to client
        self.finish()

    def getPromptAliasJson(self, clientJson):
        if clientJson["lang"] == "ch":
            # model = chinese_model
            model = None
        else:
            model = None
        type2alias_list = prompt_with_json(model, clientJson)
        dict_reply = {"reply_get_prompt_alias": {"type2alias_list": type2alias_list}}
        jsonReply = json.dumps(dict_reply, ensure_ascii=False)
        return jsonReply

    def getCorefAliasJson(self, clientJson):
        if clientJson["lang"] == "ch":
            mention2ids = bd_mention2ids
            id2coref_alias = bd_id2coref_alias
        else:
            mention2ids = wiki_mention2ids
            id2coref_alias = wiki_id2coref_alias
        alias_list, raw_chains = coref_with_json(id2coref_alias, mention2ids, clientJson)
        dict_reply = {"reply_get_coref_alias": {"alias_list": alias_list, "raw_chains": raw_chains}}
        jsonReply = json.dumps(dict_reply, ensure_ascii=False)
        return jsonReply

    def getDictAliasJson(self, clientJson):
        if clientJson["lang"] == "ch":
            id2mention = bd_id2mention
            mention2ids = bd_mention2ids
        else:
            id2mention = wiki_id2mention
            mention2ids = wiki_mention2ids
        alias_list = dict_with_json(id2mention, mention2ids, clientJson)
        dict_reply = {"reply_get_dict_alias": {"alias_list": alias_list}}
        jsonReply = json.dumps(dict_reply, ensure_ascii=False)
        return jsonReply

    def getRequestTypeFromClientJson(self, clientJson):
        if 'request_get_prompt_alias' in clientJson:
            requestType = TYPE_GET_PROMPT_ALIAS
        elif 'request_get_coref_alias' in clientJson:
            requestType = TYPE_GET_COREF_ALIAS
        elif 'request_get_dict_alias' in clientJson:
            requestType = TYPE_GET_DICT_ALIAS
        else:
            requestType = TYPE_ERROR

        if 'clientId' in clientJson:
            clientId = clientJson['clientId']
        else:
            # requestType = TYPE_ERROR
            clientId = None

        return requestType, clientId

    def getErrorJson(self, error):
        return {"err": error}


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[(r"/", IndexHandler), (r"/alias", PostHandler)],
        # template_path="/home/tsq/ybb/WebApp/client",
        # static_path="/home/tsq/ybb/WebApp/client"
        template_path="/home/tsq/ybb/WebApp/client/client_01",
        static_path="/home/tsq/ybb/WebApp/client/client_01"
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
