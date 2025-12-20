#############################################
#  Imorts
#############################################

import os
import csv
import copy
import numpy as np
import random

#############################################
#  Class Parameter
#############################################
class Parameter:
    def __init__(self):
        self.output_dir_path   = "output"#output file's path
        self.nv=1#variable definition of nv = number of varialbes (tentatively 1)
        self.nf=1#variable definition of nf = number of functions (tentatively 1)
        self.nd=1#variable definition of nd = number of data (tentatively 1)
        self.nconv=1#variable definition of ncounb= number of convolution (tentatively 1)
#############################################
#  Class for Input Data
#############################################
class InputData:
    __slots__ = [ 
        'var_list',
        'func_list',
        'w',
        'c',
        'r',
        'coef',
        'baseradius',
        'needdata',
        'sameratio',
        'baselambda',
        'minlist',
        'maxlist',
        'salist'
        ]
    #------------------------------------------------------
    def __init__(self):
        self.var_list = np.array([])
        self.func_list = np.array([])
        self.w=np.array([])
        self.c=np.array([])
        self.r=np.array([])
        self.coef=np.array([])
        self.baseradius=np.array([])
        self.baselambda=np.array([])
        self.needdata=np.array([])
        self.sameratio=np.array([])
        self.minlist=np.array([])
        self.maxlist=np.array([])
        self.salist=np.array([])
        
def readInputFile(filePath, param,data):
    file = open(filePath, 'r')
    fr = csv.reader(file)
    #inputd=[]
    line=next(fr)
    param.nd=int(line[0])
    print(param.nd)
    aa=0
    for i in range(param.nd):
        line=next(fr)
        if aa==0:
            param.nv=len(line)-1
            aa=1
        d=[]
        for j in range(param.nv):
            d=np.append(d,float(line[j]))
        data.var_list=np.append(data.var_list,d)
        data.func_list=np.append(data.func_list,float(line[param.nv]))
        print(data.func_list)
    data.var_list=np.reshape(data.var_list,[param.nd,param.nv])
    print(data.var_list)
    print(data.func_list)

def RBF(x,c,r,Lambda,y):
    nv=int(len(x[0]))
    ndata=int(len(x))
    nbasis=int(len(c))
    w=[]
    h=[]
    a=[]
    b=[]
    for i in range(nbasis):
        line=[]
        for j in range(ndata):
            dis=0.0
            for k in range(nv):
                dis+=float(-(x[j][k]-c[i][k])**2/r[k]**2)
            line.append(np.exp(dis))
        line=copy.deepcopy(line)
        h.append(line)
    h=np.array(h)
    a=np.dot(h,h.T)    
    for i in range(nbasis):
        a[i][i]+=Lambda
    b=np.linalg.inv(a)
    a=np.dot(b,h)
    w=np.dot(a,y)
    w=copy.deepcopy(w)
    print("inside RBF")
    del a
    del b
    del line
    del h
    return w
def calcrbf(x,w,c,r):
    ndv=len(x)
    nbasis=len(c)
    func=0.0
    for i in range(nbasis):
        dis=0.0
        for k in range(ndv):
            dis+=((x[k]-c[i][k])/r[k])**2
        func+=w[i]*np.exp(-dis)
    return float(func)
def errorestimate(x,y,w,c,r):
    ndata=len(x)
    nbasis=len(c)
    ndv=len(x[0])
    err=0.0
    for i in range(ndata):
        func=calcrbf(x[i],w,c,r)
        err+=(y[i]-func)**2
    return err
def distance(a,b,r):
    ndv=len(a)
    dis=0.0
    for i in range(a):
        dis+=((a[i]-b[i])/r[i])**2
    return dis

if __name__ == '__main__':
    #file=open("Approximation.csv","w")
    param = Parameter()
    inputData=InputData()
    os.makedirs(param.output_dir_path, exist_ok=True)
    fname="input.csv"#input()##################################################################Change
    readInputFile(str(fname),param,inputData)
    print(str(param.nv)+" "+str(param.nd)+" "+str(param.nconv))

