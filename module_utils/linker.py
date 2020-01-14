# -*- coding: utf-8 -*-
# @Author: rjezequel
# @Date:   2019-12-20 09:18:14
# @Last Modified by:   ronanjs
# @Last Modified time: 2020-01-14 10:53:41

import requests
import pickle
import json
import re
import os


class Linker:

    def __init__(self, datamodel):
        self.datamodel = datamodel
        self._verbose = False

    def verbose(self):
        self._verbose = True

    def log(self, m):
        if self._verbose:
            print("[linker] " + m)

    def resolve(self, ref, current=None, parent=None):

        root = self.datamodel.root

        ref = ref.lower()
        if ref == "/project":
            if "project1" in root:
                return root["project1"]
            return None

        if ref[:2] == "./":
            if current == None:
                return None
            current = current
            ref = ref[2:]

        if ref[:3] == "../":
            if parent == None:
                if current != None:
                    parent = current.parent
            if parent == None:
                return None
            current = parent
            ref = ref[3:]

        if ref[:1] == "/":
            if "project1" in root:
                current = root["project1"]
                ref = ref[1:]

        if current == None:
            self.log("Can not find object %s --- curent in None!!!! [%s]" %
                     (ref, ref[:1]))
            return None

        self.log("Looking for %s from %s>%s" % (ref, parent, current))

        selection = NodeSelector(current)

        for element in ref.lower().split("/"):

            #Look for, eg "port[name=port1]" or "port[*]"
            #/port[name=Port1]/EmulatedDevice[*]/Ipv4If

            attrKey = None
            attrVal = None
            match = re.findall("([a-zA-Z]+)\\[(.*?)\\]", element)

            if len(match) == 1:
                match = match[0]
                p = match[1].split("=")
                attrKey = p[0]
                attrVal = p[1] if len(p) > 1 else None
                element = match[0]

            elif len(match) != 0:
                raise Exception("reference syntax error: '%s' from '%s'" %
                                (element, ref))

            if selection.select(element, attrKey, attrVal) == 0:
                self.log("| Can not find object %s from %s [%s]" %
                         (ref, current, ref[:1]))
                return None

        self.log("%s from %s -> %s" % (ref, current, selection))
        return selection.firstNode()


class NodeSelector:

    def __init__(self, node):
        self.nodes = [node]

    def log(self, m):
        # print("[selector] " + m)
        pass

    def __str__(self):
        s = ""
        for node in self.nodes:
            s += "," if len(s) > 0 else ""
            s += str(node)
        return "[" + s + "]"

    def count(self):
        return self.nodes

    def firstNode(self):
        return self.nodes[0]

    def select(self, element, attrKey=None, attrVal=None):

        selection = []
        for node in self.nodes:

            for node in node.children.values():

                # self.log("| Checking object=%s"%node)
                attr = node.attributes

                if not ("object_type" in attr):
                    self.log("| Checking object=%s -> No object type!!" %
                             (node))
                    continue

                objType = attr["object_type"]

                # self.log("| Checkingtype=%s  attribute=%s -> looking for type '%s'"%(attr["object_type"],attrKey,ref))

                if objType.lower() == element:

                    if attrKey != None and attrKey != "*":

                        if not (attrKey in attr):
                            self.log(
                                "| Checking object=%s -> No such attribute %s" %
                                (node, attrKey))
                            continue

                        if attr[attrKey].lower() != attrVal:
                            self.log(
                                "| Checking object=%s -> Wrong attribute %s: %s!=%s"
                                %
                                (node, attrKey, attr[attrKey].lower(), attrVal))
                            continue

                    self.log("| Checking object=%s -> Using it" % (node))
                    selection.append(node)

                else:

                    self.log("| Checking object=%s -> Wrong type" % (node))

        self.nodes = selection
        return len(selection)
