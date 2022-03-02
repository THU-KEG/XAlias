import bminf
import json
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
import WebApp.server.params as params
from demo.call import prompt_with_json
import logging

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s')  #

define("port", default=8000, help="run on the given port", type=int)
# request types
TYPE_ERROR = -1
TYPE_GET_PROMPT_ALIAS = 0

# m_infoManager = InfoManager()

# load model
chinese_model = bminf.models.CPM2(device=params.gpu_id)


class IndexHandler(tornado.web.RequestHandler):
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
            logging.debug('Got requestType: ' + str(requestType))
            # if client sent an unknown json:
            if requestType == TYPE_ERROR:
                returnJson = self.getErrorJson('Undefined JSON received.')
            else:
                # m_infoManager.createClient(clientId)
                if requestType == TYPE_GET_PROMPT_ALIAS:
                    returnJson = self.getPromptAliasJson(clientJson)
                else:
                    returnJson = self.getErrorJson('Undefined requestType received.')

        except Exception as e:
            logging.error('Caught error from unknown location: ' + str(e))
            returnJson = self.getErrorJson('Please try again. General error: ' + str(e))

        logging.debug('Sending JSON data: ' + str(returnJson))

        self.write(returnJson)  # send JSON to client

    def getPromptAliasJson(self, clientJson):
        if clientJson["lang"] == "ch":
            model = chinese_model
        else:
            model = None
        alias_list = prompt_with_json(model, clientJson)
        dict_reply = {"reply_get_prompt_alias": {"alias_list": alias_list}}
        jsonReply = json.dumps(dict_reply, ensure_ascii=False)
        return jsonReply

    def getRequestTypeFromClientJson(self, clientJson):
        if 'request_get_prompt_alias' in clientJson:
            requestType = TYPE_GET_PROMPT_ALIAS
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


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[(r"/", IndexHandler)])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
