# -*- coding: utf-8 -*-
"""Micro-service for CQP API."""
import json

import falcon

from cqpapi import Cqp, con_source


class CWBResource:
    """Resource for CWB."""

    def on_get(self, req, resp):
        """GET method."""
        corpus_names = req.get_param('corpus_names', required=True).split(',')
        token = req.get_param('token', required=True)
        window_size = int(req.get_param('window_size', default=8))
        rsize = int(req.get_param('rsize', default=0)) or None
        show_pos = req.get_param_as_bool('show_pos', required=True)

        conclst = []
        for corpus_name in corpus_names:
            cqp = Cqp(corpus_name=corpus_name,
                      window_size=window_size)
            cqp.find(token=token,
                     rsize=rsize,
                     show_pos=show_pos)
            conclst += cqp.conclst

        resp.body = json.dumps(conclst)
        resp.content_type = falcon.MEDIA_JSON


class ConSourceResource:
    """Concordance Source."""

    def on_get(self, req, resp):
        """GET method."""
        qpos = req.get_param('qpos')
        resp.body = con_source(qpos)


api = falcon.API()
api.add_route('/cwb', CWBResource())
api.add_route('/con_source', ConSourceResource())
