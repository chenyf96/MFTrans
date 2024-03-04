# coding=gbk
from __future__ import print_function

import csv
import os

import esm
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
# import tensorflow as tf
import warnings
import cmath
import string
from einops import rearrange

h_sp = 0
h_sn = 0
h_mcc = 0
h_acc = 0
warnings.filterwarnings('ignore')

learning_rate = 1e-4
Max_length = 100

# �޸����ݼ��������ģ��
load_model_name = 'complex-1.25-msa-concat.model'
dataset_path = '/data0/cyf/SPOT-1D-Single/data_CASP11/'
# dataset_path = '/data0/cyf/cb513/'
# dataset_path = '/data0/cyf/SPOT-1D-Single/data_TEST2016/'
# dataset_path = '/home/chenyifu/project/PSSP/cxdatabase/debug/'
# �޸ĵ�ǰ����Ŀ¼
os.chdir(dataset_path)

import torch.utils.data as data
import torch

batchsize = 1
lamda = 0.1
import datetime

print(datetime.datetime.now())
np.set_printoptions(threshold=np.inf)

# ��ȡmsa dataset

MAX_MSA_ROW_NUM = 256
MIN_MSA_ROW_NUM = 16
MAX_MSA_COL_NUM = 100
msa_row_num = 256

# ��ȡ��ǰ·��
cwd = os.getcwd()
msa_path = './msa/'
# �޸ĵ�ǰ����Ŀ¼
os.chdir(msa_path)
# �����ļ����µ������ļ��������б�
csv_name_list = os.listdir()
csv_name_list.sort(key=lambda x: int(x.split('.')[0]))  # �����������ܹؼ�
test_num = len(csv_name_list)
print("Tesing number:", test_num)
# ��ȡ��һ��CSV�ļ���������ͷ�����ں�����csv�ļ�ƴ��
# msa_name = pd.read_csv(csv_name_list[0])
# ѭ�������б��и���CSV�ļ�����������ļ�ƴ��

# ����msa test dataset
print('Loading msa test data...')
msat_list = []
for i in range(0, test_num):  # ��ȡ977�����ݼ�
    seqs = []
    table = str.maketrans(dict.fromkeys(string.ascii_lowercase))
    with open(csv_name_list[i], "r") as f:  # ����ֻ�Ƕ�ȡ�����ļ�
        lines = f.readlines()
    # read file line by line
    for j in range(0, len(lines), 2):
        seq = []
        seq.append(lines[j])
        seq.append(lines[j + 1].rstrip().translate(table))
        seqs.append(seq)

    if msa_row_num > MAX_MSA_ROW_NUM:
        msa_row_num = MAX_MSA_ROW_NUM
        print(f"The MSA row num is larger than {MAX_MSA_ROW_NUM}. This program force the msa row to under {MAX_MSA_ROW_NUM}")

    seqs = seqs[: msa_row_num]
    # A_Prot ԭ���� return seqs, seqs[0]  # msa_seq, query_seq
    # seqs��һ��list���ܳ�256��ÿ����list���涼�����seqs[0]��[Ŀ�����֣������ṹ]��������[��ѯ������֣������ṹ]
    msat_list.append(seqs)
print('Loading msa test data over')

# ����pssm-csv

# ��ȡ��ǰ·��
cwd = os.getcwd()
read_path = '../pssm/'
# �޸ĵ�ǰ����Ŀ¼
os.chdir(read_path)
# �����ļ����µ������ļ��������б�
csv_name_list = os.listdir()
csv_name_list.sort(key=lambda x: int(x.split('.')[0]))
# ��ȡ��һ��CSV�ļ���������ͷ�����ں�����csv�ļ�ƴ��
protein = pd.read_csv(csv_name_list[0])
# ѭ�������б��и���CSV�ļ�����������ļ�ƴ��

# pssm���Լ�
print('Loading pssm test data...')
for i in range(0, test_num):
    # print(i,"/",test_num)
    # print(csv_name_list[i])
    protein = pd.read_csv(csv_name_list[i])
    seqt = pd.read_csv(csv_name_list[i],usecols=[1]).transpose()
    seqt = seqt.values.tolist()
    seqt=sum(seqt,[])
    # print(len(seq))
    x = protein[['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y']]
    y = protein['HEC']
    y = list(y)
    for k in range(0, len(y)):
        y[k] = ord(y[k]) - 65  # ��0��ʼ
        if y[k] == 7:
            y[k] = 1;
        elif y[k] == 4:
            y[k] = 2;
        elif y[k] == 2:
            y[k] = 3;
    for j in range(0, len(seqt)):
        seqt[j] = ord(seqt[j]) - 64  # ��0��ʼ
        if seqt[j] == 25:
            seqt[j] = seqt[j] - 5
        elif 22 <= seqt[j] <= 23:
            seqt[j] = seqt[j] - 4

        elif 16 <= seqt[j] <= 20:
            seqt[j] = seqt[j] - 3

        elif 11 <= seqt[j] <= 14:
            seqt[j] = seqt[j] - 2

        elif 3 <= seqt[j] <= 9:
            seqt[j] = seqt[j] - 1
        elif seqt[j] == 1:
            seqt[j] = seqt[j]
    classes = 3
    reallength = [len(y)]
    if (len(y) > Max_length):
        reallength = [Max_length]
    # print('seq',seq)

    if (len(x) > Max_length):
        x = x[:Max_length]
    x = np.array(x)
    x = torch.from_numpy(x)
    # x = torch.unsqueeze(x,0)
    # x = torch.unsqueeze(x,0).float()
    # m = nn.ReflectionPad2d((0, 0, 0, 1))
    # x = m(x)
    # x = x.squeeze()
    # print("pssm x", i)
    seqt=np.array(seqt)
    if (len(seqt) < Max_length + 1):
        seqt = np.pad(seqt, (0, Max_length - len(seqt)), 'constant')
    if (len(x) < Max_length + 1):
        x = np.pad(x, ((0, Max_length - len(x)), (0, 0)), 'constant')
    if (len(y) > Max_length):
        y = y[:Max_length]
    if (len(seqt) > Max_length):
        seqt =seqt[:Max_length]
    y = np.array(y)  # y���������͵ı�ǩ
    y = torch.from_numpy(y)
    y = torch.unsqueeze(y, dim=1)
    y = y.type(torch.LongTensor)
    y = torch.zeros(Max_length, 4).scatter_(1, y, 1)
    # # print(y.shape)
    # y = torch.unsqueeze(y,0)
    # y = torch.unsqueeze(y,0).float()
    # y = m(y)
    # y = y.squeeze()
    # # print("pssm y", i)
    # if (len(y) < Max_length+1):
    #     y = np.pad(y, ((0, Max_length +1- len(y)), (0, 0)), 'constant')
    # print(y.shape)
    if (i == 0):
        x1t = x
        y1t = y
        reallength1t = reallength
        seq1t=seqt
    if (i != 0):
        x1t = np.concatenate((x1t, x), axis=0)
        y1t = np.concatenate((y1t, y), axis=0)
        reallength1t = np.concatenate((reallength1t, reallength), axis=0)
        seq1t=np.concatenate((seq1t,seqt),axis=0)
    # print('pssm:%d' % i)
    # print('length:%d' % (len(x1)))

# print(x1t.shape)
x1t = torch.from_numpy(x1t);
x1t = x1t.view(test_num, Max_length, 20)
# print("x1t",x1t.shape)
y1t = np.delete(y1t, 0, axis=1)
y1t = torch.from_numpy(y1t);
y1t = y1t.view(test_num, Max_length, 3)
seqt=torch.from_numpy(seq1t)
seqt = seqt.view(test_num, Max_length)
# print("y1t",y1t.shape)
# print("reallengtht",reallength1t)
print('Loading pssm test data over')

# ����hmm-csv
# hmmѵ����
cwd = os.getcwd()
read_path = '../hmm/'
os.chdir(read_path)
csv_name_list = os.listdir()
csv_name_list.sort(key=lambda x: int(x.split('.')[0]))
protein = pd.read_csv(csv_name_list[0])

# hmm���Լ�
print('Loading hmm test data...')
for i in range(0, test_num):
    protein = pd.read_csv(csv_name_list[i])
    x = protein[['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y']]
    if len(x) > Max_length:
        x = x[:Max_length]
    x = np.array(x)
    x = torch.from_numpy(x)
    # x = torch.unsqueeze(x, 0)
    # x = torch.unsqueeze(x, 0).float()
    # m = nn.ReflectionPad2d((0, 0, 0, 1))
    # x = m(x)
    # x = x.squeeze()
    # print("pssm x", i)
    if (len(x) < Max_length + 1):
        x = np.pad(x, ((0, Max_length - len(x)), (0, 0)), 'constant')
    if (i == 0):
        x2t = x
    if (i != 0):
        x2t = np.concatenate((x2t, x), axis=0)
        # print('hmm : %d' % i)
# print(x2t.shape)
x2t = torch.from_numpy(x2t);
x2t = x2t.view(test_num, Max_length, 20)
# print("x2t", x2t.shape)
print('Loading hmm test data over')

cwd = os.getcwd()
read_path = '/home/chenyifu/project/PSSP/concat2_model'
os.chdir(read_path)


def cosine(x, y):
    y=torch.transpose(y,1,2)
    value = torch.matmul(x, y)
    n = torch.norm(input=value, p=float('inf'))
    return value / n


class bigru_attention(nn.Module):
    def __init__(self, input_dim, hidden_dim, layer_dim):
        super(bigru_attention, self).__init__()
        self.hidden_dim = hidden_dim
        self.bigru = nn.LSTM(input_dim, hidden_dim, num_layers=layer_dim, bidirectional=True, batch_first=True)
        self.weight_W = nn.Parameter(torch.Tensor(self.hidden_dim * 2, self.hidden_dim * 2))
        self.weight_proj = nn.Parameter(torch.Tensor(self.hidden_dim * 2, 1))
        self.fc = nn.Linear(self.hidden_dim * 2, self.hidden_dim * 2)
        nn.init.uniform_(self.weight_W, -0.1, 0.1)
        nn.init.uniform_(self.weight_proj, -0.1, 0.1)

    def forward(self, x, trainstate=True):
        gru_out, _ = self.bigru(x)
        u = torch.tanh(torch.matmul(gru_out, self.weight_W))
        att = torch.matmul(u, self.weight_proj)
        att_score = F.softmax(att, dim=1)

        scored_x = gru_out * att_score

        y = self.fc(scored_x)
        return y


def conv2d(in_chan, out_chan, kernel_size, dilation=1, **kwargs):
    padding = dilation * (kernel_size - 1) // 2
    return nn.Conv2d(in_chan, out_chan, kernel_size, padding=padding, dilation=dilation, **kwargs)


def instance_norm(filters, eps=1e-6, **kwargs):
    return nn.InstanceNorm2d(filters, affine=True, eps=eps, **kwargs)


def elu():
    return nn.ELU(inplace=True)


def relu():
    return nn.ReLU(inplace=True)


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.restriction = torch.zeros([batchsize, Max_length, 3])
        self.embedding = nn.Embedding(25, 20)
        self.fnn1_1 = nn.Linear(in_features=240, out_features=512)
        
        self.padding1d = nn.ReflectionPad1d((1, 1))
        self.conv1d = nn.Conv1d(in_channels=Max_length, out_channels=Max_length, kernel_size=3, stride=1)
        self.pooling1d = nn.MaxPool1d(kernel_size=3, stride=1)

        # self.unsqueeze=torch.unsqueeze(self,dim=1)
        self.padding2d = nn.ReflectionPad2d((1, 1, 1, 1))
        self.conv2d_1 = nn.Conv2d(in_channels=1, out_channels=1, kernel_size=3, stride=1, padding=1)
        self.conv2d_2 = nn.Conv2d(in_channels=1, out_channels=1, kernel_size=3, stride=1, padding=1)
        self.conv2d_3 = nn.Conv2d(in_channels=1, out_channels=1, kernel_size=3, stride=1, padding=1)
        self.padding2d1_2 = nn.ReflectionPad2d((1, 1, 1, 1))
        self.pooling2d = nn.MaxPool2d(kernel_size=3, stride=1, padding=1)
        # self.squeeze=torch.squeeze()
        # self.attgru1_1=bigru_attention(input_dim=128,hidden_dim=128,layer_dim=1)
        # self.attgru2_1 = bigru_attention(input_dim=256, hidden_dim=256, layer_dim=1)
        # self.attgru1_2 = bigru_attention(input_dim=128, hidden_dim=128, layer_dim=1)
        # self.attgru2_2 = bigru_attention(input_dim=256, hidden_dim=256, layer_dim=1)
        # self.attgru1_3 = bigru_attention(input_dim=128, hidden_dim=128, layer_dim=1)
        # self.attgru2_3 = bigru_attention(input_dim=256, hidden_dim=256, layer_dim=1)

        self.bgru1 = nn.LSTM(input_size=512, hidden_size=512, num_layers=1, bidirectional=True, batch_first=True)

        self.replayer1 = nn.Linear(in_features=1024, out_features=3)
        # self.replayer2=nn.Linear(in_features=128,out_features=3)
        self.fnn4 = nn.Linear(in_features=1024, out_features=512)

        self.bgru2 = nn.LSTM(input_size=512, hidden_size=512, num_layers=1, bidirectional=True, batch_first=True)

        self.fnn3_1 = nn.Linear(in_features=1024, out_features=512)
        self.fnn3_2 = nn.Linear(in_features=512, out_features=128)
        self.fnn3_3 = nn.Linear(in_features=128, out_features=3)

        self.relu = nn.ReLU(inplace=True)
        self.softmax = nn.Softmax(dim=2)
        self.batchnorm = nn.BatchNorm2d(num_features=1)

        # self.transformer_layer=nn.TransformerEncoderLayer()
        self.transformer_layer = nn.TransformerEncoderLayer(d_model=512, nhead=8)
        self.transformer = nn.TransformerEncoder(self.transformer_layer, num_layers=6)

        self.filters = 64
        self.kernel = 3
        self.num_layers = 61

        self.linear_proj = nn.Sequential(
            nn.Linear(768, 384),
            nn.InstanceNorm1d(384),
            relu(),
            nn.Linear(384, 192),
            nn.InstanceNorm1d(192),
            relu(),
            nn.Linear(192, 128),
        )

        self.first_block = nn.Sequential(
            conv2d(400, 256, 1),
            instance_norm(256),
            relu(),
            conv2d(256, 128, 1),
            instance_norm(128),
            relu(),
            conv2d(128, self.filters, 1),
            instance_norm(self.filters),
            relu(),
        )
        self.fnn1_2 = nn.Linear(in_features=640, out_features=512)

    def forward(self, pssm, hmm, seq, msa_query_embeddings, msa_row_attentions, trainstate=True):
        # msa_query_embeddings.shape =  torch.Size([1, 100, 768])
        # msa_row_attentions.shape =  torch.Size([1, 12, 12, 100, 100])
        msa_query_embeddings = self.linear_proj(msa_query_embeddings)  # msa_query_embeddings.shape =  torch.Size([1, 100, 128])
        msa_query_embeddings = msa_query_embeddings.permute((0, 2, 1))  # msa_query_embeddings.shape =  torch.Size([1, 128, 100])

        msa_query_embeddings_row_expand = msa_query_embeddings.unsqueeze(2).repeat(1, 1, msa_query_embeddings.shape[-1],1)
        # msa_query_embeddings_row_expand.shape =  torch.Size([1, 128, 100, 100])
        msa_query_embeddings_col_expand = msa_query_embeddings.unsqueeze(3).repeat(1, 1, 1, msa_query_embeddings.shape[-1])
        # msa_query_embeddings_col_expand.shape =  torch.Size([1, 128, 100, 100])
        msa_query_embeddings_out_concat = torch.cat([msa_query_embeddings_row_expand, msa_query_embeddings_col_expand],dim=1)
        # msa_query_embeddings_out_concat.shape =  torch.Size([1, 256, 100, 100])

        msa_row_attentions = rearrange(msa_row_attentions, 'b l h i j -> b (l h) i j')
        # msa_row_attentions.shape =  torch.Size([1, 144, 100, 100])
        msa_row_attentions_symmetrized = 0.5 * (msa_row_attentions + msa_row_attentions.permute((0, 1, 3, 2)))
        # msa_row_attentions_symmetrized.shape =  torch.Size([1, 144, 100, 100])

        conv_input = torch.cat([msa_query_embeddings_out_concat, msa_row_attentions_symmetrized], dim=1)  # conv_input.shape =  torch.Size([1, 400, 100, 100])
        conv_input = self.first_block(conv_input)  # conv_input.shape =  torch.Size([1, 64, 100, 100])

        # �������Ȱ�conv_input���յ���λ�͵���ά�ֱ�mean���õ���������concat
        conv_input_row = conv_input.mean([2])    # conv_input_row.shape =  torch.Size([1, 64, 100])
        conv_input_col = conv_input.mean([3])    # conv_input_col.shape =  torch.Size([1, 64, 100])
        
        conv_input = torch.cat([conv_input_row, conv_input_col], dim=1)  # conv_input.shape =  torch.Size([1, 128, 100])
        conv_input = conv_input.permute((0, 2, 1))        # conv_input.shape =  torch.Size([1, 100, 128])

        ########## ����Ϊ����ӵ�msa transformer��������
        seq = self.embedding(seq.long())  # [1,100] -> [1,100,20],pssm=[1,100,20],hmm=[1,100,20]
        ps = cosine(pssm, seq)            # [1,100,100]
        hs = cosine(hmm, seq)             # [1,100,100]

        x = torch.cat((pssm, hmm, ps, hs), 2)  # [1,100,240]
        x = self.fnn1_1(x)  # [1,100,512]
        
        x = torch.cat([x, conv_input], dim=2)  # msa transformer����������ԭ����ƴ������ concat�������x.shape =  torch.Size([1, 100, 512+128=640])
        x = self.fnn1_2(x)  # [1,100,512]
        
        x = F.dropout(input=x, training=trainstate)
        x = self.relu(x)

        x = torch.unsqueeze(input=x, dim=0)
        x = self.batchnorm(x)

        x = self.conv2d_1(x)
        x = self.batchnorm(x)
        x = self.relu(x)

        x = self.conv2d_2(x)
        x = self.batchnorm(x)
        x = self.relu(x)

        x = self.conv2d_3(x)
        x = self.relu(x)

        x = self.pooling2d(x)
        x = self.relu(x)
        x = self.batchnorm(x)
        x = torch.squeeze(x, 1)

        # x3 = x[:, 60:100, :]
        # x1 = x[:, 0:50, :]
        # x2 = x[:, 50:100, :]
        # x1 = self.attgru1_1(x1)
        # x2 = self.attgru1_2(x2)
        # x3 = self.attgru1_3(x3)
        # x = torch.cat([x1, x2,x3], dim=1)
        print('before bgru1', x.shape)
        x, _ = self.bgru1(x)
        print('after bgru1', x.shape)
        # x = torch.cat([x1, x2], dim=1)
        x = torch.unsqueeze(input=x, dim=0)
        x = self.batchnorm(x)
        x = torch.squeeze(input=x, dim=0)
        x = self.relu(x)

        r = self.replayer1(x)
        # r=self.relu(r)
        # r=self.replayer2(r)

        r = self.softmax(r)
        self.restriction = r
        x = self.fnn4(x)

        # x1 = x[:, 0:50, :]
        # x2 = x[:, 50:100, :]
        print('before bgru2', x.shape)
        x, _ = self.bgru2(x)
        print('after bgru2', x.shape)
        # x2, _ = self.bgru2_2(x2)
        # x = torch.cat([x1, x2], dim=1)

        x = torch.unsqueeze(input=x, dim=0)
        x = self.batchnorm(x)
        x = torch.squeeze(input=x, dim=0)
        x = self.relu(x)

        # x1 = x[:, 0:30, :]
        # x2 = x[:, 30:60, :]
        # x3 = x[:, 60:100, :]
        # x1 = self.attgru2_1(x1)
        # x2 = self.attgru2_2(x2)
        # x3 = self.attgru2_3(x3)
        # x = torch.cat([x1, x2, x3], dim=1)

        x = self.fnn3_1(x)

        x = self.transformer(x)

        x = self.relu(x)
        x = self.fnn3_2(x)
        x = self.fnn3_3(x)

        x = self.softmax(x)
        # x = self.final(x)
        # x = self.softmax(x)
        return x

    def get_rep_layer(self):
        return self.restriction


class restricted_loss(nn.Module):
    def __init__(self):
        super().__init__()
        # self.crossentropy=nn.CrossEntropyLoss()

    def forward(self, output, tar, rep, who):
        # loss1=self.crossentropy(torch.sigmoid(output),torch.sigmoid(target).long())
        # loss2= self.crossentropy(torch.sigmoid(output), torch.sigmoid(target).long())
        # print('output1', output)
        w = torch.tensor([1., 1.25, 1.]).to(device)
        tar = tar * w
        # output=output*w
        # print('output2',output)
        loss1 = F.mse_loss(output.float(), tar.float(), reduction='mean')
        loss2 = F.mse_loss(rep.float(), tar.float(), reduction='mean')
        # loss2 = self.crossentropy(output, target.long())

        # loss1=F.mse_loss(input=output.float(),target=target.float(),reduction='mean')
        # loss2=F.mse_loss(input=rep.float(),target=target.float(),reduction='mean')
        loss = loss1 + lamda * loss2
        # print('-----------------------loss','for',who,'------------------------------------------')
        # print(datetime.datetime.now())
        # print('loss1:',loss1.cpu())
        # print('rep loss:',loss2.cpu())
        # print('-----------------------loss','for',who,'------------------------------------------')
        return loss


bgru1 = 0.0


def accuracy(x_1,x_2,x_3,i,j,reallength1,label,epoch,who):
    with torch.no_grad():
        x1=x_1.detach().numpy()
        x2=x_2.detach().numpy()
        x3=x_3.detach().numpy()


        # total number of real H,E,C
        H_count=0.0
        E_count=0.0
        C_count=0.0
        # predict right of H,E,C
        H=0
        E=0
        C=0
        #
        def likely(x1,x2,x3):
            HEC=1
            temp=0
            if(x1>x2):
                temp=x1
                HEC=1
            elif(x1<x2):
                temp=x2
                HEC=2
            if(temp>x3):
                temp=temp
                HEC=HEC
            elif(temp<x3):
                temp=x3
                HEC=3
            return temp,HEC

        def sov(x_1, x_2, x_3, i, j, reallength1, label):
            with torch.no_grad():
                x1 = x_1.detach().numpy()
                x2 = x_2.detach().numpy()
                x3 = x_3.detach().numpy()
                # total number of real H,E,C
                H_count = 0.0
                E_count = 0.0
                C_count = 0.0

                H=0
                E=0
                C=0
                H1 = 0
                E1 = 0
                C1 = 0
                H2 = 0
                E2 = 0
                C2 = 0
                H3 = 0
                E3 = 0
                C3 = 0

                flag=0
                sovh=0
                sove=0
                sovc=0

                for k in range(0, reallength1[i * 1 + j]):
                    if (label[j][k][0] == 1):
                        H_count = H_count + 1
                    if (label[j][k][1] == 1):
                        E_count = E_count + 1
                    if (label[j][k][2] == 1):
                        C_count = C_count + 1
                for k in range(0, reallength1[i * 1 + j]):
                    _, kind = likely(x1[k], x2[k], x3[k])
                    if (label[j][k][0] == 1 and kind == 1):
                        H = H + 1
                    if (label[j][k][1] == 1 and kind == 2):
                        E = E + 1
                    if (label[j][k][2] == 1 and kind == 3):
                        C = C + 1
                H1 = E1 = C1 = 0
                for k in range(0, reallength1[i * 1 + j]):
                    if (label[j][k][0] == 1):
                        H1 = H1 + 1
                    if (label[j][k][1] == 1):
                        E1 = E1 + 1
                    if (label[j][k][2] == 1):
                        C1 = C1 + 1
                H2 = E2 = C2 = 0
                for k in range(0, reallength1[i * 1 + j]):
                    _, kind = likely(x1[k], x2[k], x3[k])
                    if (kind == 1):
                        H2 = H2 + 1
                    if (kind == 2):
                        E2 = E2 + 1
                    if (kind == 3):
                        C2 = C2 + 1
                length = float(H_count + E_count + C_count)
                mini = float(H + E + C)
                maxh = H1 + H2 - H
                maxe = E1 + E2 - E
                maxc = C1 + C2 - C
                max = float(maxh + maxe + maxc)
                dec = min(maxc - C, C, 0.5 * C_count, 0.5 * C)
                deh = min(maxh - H, H, 0.5 * H_count, 0.5 * H)
                dee = min(maxe - E, E, 0.5 * E_count, 0.5 * E)

                if(maxe!=0):
                    sove = ((E + dee) / maxe)
                else:
                    flag=1

                if (maxh != 0):
                    sovh = ((H + deh) / maxh)
                else:
                    flag = 1
                if (maxc != 0):
                    sovc = ((C + dec) / maxc)
                else:
                    flag = 1

                sov = (sovc + sove + sovh)/ 3
            return sovh, sove, sovc, sov,flag
        for k in range(0,reallength1[i*batchsize+j]):

            if(label[j][k][0]==1):
                H_count=H_count+1
            if(label[j][k][1]==1):
                E_count=E_count+1
            if(label[j][k][2]==1):
                C_count=C_count+1
        for k in range(0,reallength1[i*batchsize+j]):
            # print("x1[k]",x1[k])

            _,kind=likely(x1[k],x2[k],x3[k])
            if (label[j][k][0] == 1 and kind==1):
                H = H + 1
            if (label[j][k][1] == 1 and kind==2):
                E = E + 1
            if (label[j][k][2] == 1 and kind==3):
                C = C + 1
        sov_h,sov_e,sov_c,sov_overall,flag=sov(x_1=x_1,x_2=x_2,x_3=x_3,i=i,j=j,label=label,reallength1=reallength1)
        TP = 0
        FP = 0
        TN = 0
        FN = 0
        H_TP = 0
        H_FP = 0
        H_TN = 0
        H_FN = 0
        E_TP = 0
        E_FP = 0
        E_TN = 0
        E_FN = 0
        C_TP = 0
        C_FP = 0
        C_TN = 0
        C_FN = 0
        H_H=0
        H_E=0
        H_C=0
        E_H = 0
        E_E = 0
        E_C = 0
        C_H = 0
        C_E = 0
        C_C = 0
        for k in range(0, reallength1[i * batchsize + j]):
            # print("x1[k]",x1[k])
            _, kind = likely(x1[k], x2[k], x3[k])
            if (label[j][k][0] == 1 and kind == 1):
                H_TP = H_TP + 1
            if (label[j][k][0] != 1 and kind == 1):
                H_FP = H_FP + 1
            if (label[j][k][0] != 1 and kind != 1):
                H_TN = H_TN + 1
            if (label[j][k][0] == 1 and kind != 1):
                H_FN = H_FN + 1


            if (label[j][k][1] == 1 and kind == 2):
                E_TP = E_TP + 1
            if (label[j][k][1] != 1 and kind == 2):
                E_FP = E_FP + 1
            if (label[j][k][1] != 1 and kind != 2):
                E_TN = E_TN + 1
            if (label[j][k][1] == 1 and kind != 2):
                E_FN = E_FN + 1

            if (label[j][k][2] == 1 and kind == 3):
                C_TP = C_TP + 1
            if (label[j][k][2] != 1 and kind == 3):
                C_FP = C_FP + 1
            if (label[j][k][2] != 1 and kind != 3):
                C_TN = C_TN + 1
            if (label[j][k][2] == 1 and kind != 3):
                C_FN = C_FN + 1
#---------------------------------------------------------------------------------------
            if (label[j][k][0] == 1 and kind == 1):
                H_H = H_H + 1
            if (label[j][k][0] == 1 and kind == 2):
                H_E = H_E + 1
            if (label[j][k][0] == 1 and kind == 3):
                H_C = H_C + 1

            if (label[j][k][1] == 1 and kind == 1):
                E_H = E_H + 1
            if (label[j][k][1] == 1 and kind == 2):
                E_E = E_E + 1
            if (label[j][k][1] == 1 and kind == 3):
                E_C = E_C + 1

            if (label[j][k][2] == 1 and kind == 1):
                C_H = C_H + 1
            if (label[j][k][2] == 1 and kind == 2):
                C_E = C_E + 1
            if (label[j][k][2] == 1 and kind == 3):
                C_C = C_C + 1

        TP=(((H_count/(H_count+E_count+C_count))*H_TP)+((E_count/(H_count+E_count+C_count))*E_TP)+((C_count/(H_count+E_count+C_count))*C_TP))
        TN = (((H_count/(H_count+E_count+C_count))*H_TN)+((E_count/(H_count+E_count+C_count))*E_TN)+((C_count/(H_count+E_count+C_count))*C_TN))
        FP =(((H_count/(H_count+E_count+C_count))*H_FP)+((E_count/(H_count+E_count+C_count))*E_FP)+((C_count/(H_count+E_count+C_count))*C_FP))
        FN = (((H_count/(H_count+E_count+C_count))*H_FN)+((E_count/(H_count+E_count+C_count))*E_FN)+((C_count/(H_count+E_count+C_count))*C_FN))
        # sn = TP / (TP + FN)
        # sp = TN / (TN + FN)
        # mcc = ((TP * TN) - (FP * FN)) / (
        #     cmath.sqrt((TP + FN) * (TP + FP) * (TN + FN) * (TN + FP)))



        H_acc=0.0
        E_acc=0.0
        C_acc=0.0
        HE_acc=0.0
        HC_acc=0.0
        EC_acc=0.0
        HEC_acc=0.0
        # print('-----------------------------',who,'in',epoch,'---------------------------------------------')

        # print(datetime.datetime.now())
        # H_acc = float(H) / float(H_count)
        # E_acc = float(E) / float(E_count)
        # C_acc = float(C) / float(C_count)
        # HE_acc = (float(H)+float(E))/ (float(H_count)+float(E_count))
        # HC_acc = (float(H)+float(C) )/( float(H_count)+float(C_count))
        # EC_acc = (float(E)+float(C) )/ (float(E_count)+float(C_count))
        HEC_acc = float(H + E + C) / float(H_count + E_count + C_count)

        #     print("H with H_count",H_count , "Accuracy: ", H_acc)
        #     print("E with E_count",E_count , "Accuracy: ", E_acc)
        #     print("C with C_count",C_count , "Accuracy: ", C_acc)
        #     print("HE :", "Accuracy: ", HE_acc)
        #     print("HC :", "Accuracy: ", HC_acc)
        #     print("EC :", "Accuracy: ", EC_acc)
        #     print("HEC:", "Accuracy: ", HEC_acc)
        # print('-----------------------------', who,'in',epoch,'----------------------------------------------')

        return TP,TN,FP,FN,H_TP,H_TN,H_FP,H_FN,E_TP,E_TN,E_FP,E_FN,C_TP,C_TN,C_FP,C_FN,H_H,H_E,H_C,E_H,E_E,E_C,C_H,C_E,C_C,sov_h,sov_e,sov_c,sov_overall,flag,H,E,C,H_count,E_count,C_count



cwd = os.getcwd()
read_path = '/home/chenyifu/project/PSSP/concat2_model'
# �޸ĵ�ǰ����Ŀ¼
os.chdir(read_path)
############################################################################################################################################################

model = Net()

if torch.cuda.is_available():
    device = torch.device("cuda:0" )
    model.load_state_dict(torch.load(load_model_name,map_location=device))
    print("Loading model name :", load_model_name)
else:
    device=torch.device("cpu")
    model.load_state_dict(torch.load(load_model_name, map_location=torch.device('cpu')))
    print("Loading model name :", load_model_name)
model.to(device)


criterion = restricted_loss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

########## MSA transformer model
msa_transformer, msa_alphabet = esm.pretrained.esm_msa1b_t12_100M_UR50S()
msa_batch_converter = msa_alphabet.get_batch_converter()
msa_transformer.to(device)
for param in msa_transformer.parameters():
    param.requires_grad = False


def extract_msa_transformer_features(msa_seq, msa_transformer, msa_batch_converter, device=torch.device("cpu")):
    msa_seq_label, msa_seq_str, msa_seq_token = msa_batch_converter([msa_seq])
    msa_seq_token = msa_seq_token.to(device)
    msa_row, msa_col = msa_seq_token.shape[1], msa_seq_token.shape[2]
    # print(f"{msa_seq_label[0][0]}, msa_row: {msa_row}, msa_col: {msa_col}")

    if msa_col > MAX_MSA_COL_NUM + 1:
        # print(f"msa col num should less than {MAX_MSA_COL_NUM}. This program force the msa col to under {MAX_MSA_COL_NUM}")
        msa_seq_token = msa_seq_token[:, :, :MAX_MSA_COL_NUM + 1]
    if msa_col < MAX_MSA_COL_NUM + 1:
        # print("1111111111")
        msa_seq_token = nn.functional.pad(msa_seq_token, pad=(0, MAX_MSA_COL_NUM + 1 - msa_col, 0, 0, 0, 0),
                                          mode="constant", value=0)

    ### keys: ['logits', 'representations', 'col_attentions', 'row_attentions', 'contacts']
    msa_transformer_outputs = msa_transformer(
        msa_seq_token, repr_layers=[12],
        need_head_weights=True, return_contacts=True)
    msa_row_attentions = msa_transformer_outputs['row_attentions']
    msa_representations = msa_transformer_outputs['representations'][12]
    msa_query_representation = msa_representations[:, 0, 1:, :]  # remove start token
    msa_row_attentions = msa_row_attentions[..., 1:, 1:]  # remove start token

    return msa_query_representation, msa_row_attentions


class Test_Dataset(data.Dataset):
    def __init__(self, pssm, hmm, label, seqt):
        self.pssm = pssm
        self.hmm = hmm
        self.label = label

        self.seqt =seqt

    def __getitem__(self, index):  # ���ص���tensor
        pssm, hmm, label,seqt= self.pssm[index], self.hmm[index], self.label[index], self.seqt[index]
        return pssm, hmm, label, seqt

    def __len__(self):
        return test_num


test_dataset = Test_Dataset(x1t, x2t, y1t,seqt)
# test_dataset=MyDataset(x1,x2,reallength1t)
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batchsize, shuffle=False, drop_last=True)

acc_dict = []


def save_model(high_acc, epoch, bgru, h_acc, h_sn, h_sp, h_mcc):
    highest = high_acc
    total_acc = 0.0
    total_sn = 0
    total_sp = 0
    total_mcc = 0
    high_in_single = 0.0
    BGRU = bgru
    pred = []
    TP = 0
    TN = 0
    FP = 0
    FN = 0
    htp = 0
    htn = 0
    hfp = 0
    hfn = 0
    etp = 0
    etn = 0
    efp = 0
    efn = 0
    ctp = 0
    ctn = 0
    cfp = 0
    cfn = 0
    H_H = 0
    H_E = 0
    H_C = 0
    E_H = 0
    E_E = 0
    E_C = 0
    C_H = 0
    C_E = 0
    C_C = 0
    SOV_H = 0
    SOV_E = 0
    SOV_C = 0
    SOV = 0
    total = 0
    h = 0
    e = 0
    c = 0
    sn = 0
    sp = 0
    mcc = 0
    acc = 0
    precision = 0
    tH=0
    tE = 0
    tC = 0
    tH_count=0
    tE_count=0
    tC_count=0
    H = 0
    E = 0
    C = 0
    H_count = 0
    E_count = 0
    C_count = 0
    HEC_acc = 0

    sov_count = test_num

    for i, (test_pssm, test_hmm, test_label, label_for_loss) in enumerate(test_loader):
        # print("test_pssm",test_pssm)
        test_pssm = torch.tensor(test_pssm, dtype=torch.float32).to(device)
        test_hmm = torch.tensor(test_hmm, dtype=torch.float32).to(device)
        test_label = torch.tensor(test_label, dtype=torch.float32).to(device)
        label_for_loss = torch.tensor(label_for_loss, dtype=torch.float32).to(device)

        msa_query_representation_test, msa_row_attentions_test = extract_msa_transformer_features(msat_list[i],
                                                                                                  msa_transformer,
                                                                                                  msa_batch_converter,
                                                                                                  device=device)

        y_test = model(test_pssm, test_hmm, label_for_loss, msa_query_representation_test, msa_row_attentions_test, trainstate=False)
        # print('y_test.shape =', y_test.shape)    # y_test.shape = torch.Size([1, 100, 3])
        pred.append(y_test)
        rep_test = model.get_rep_layer()
        criterion(output=y_test, tar=test_label, rep=rep_test, who='test')

        t_TP, t_TN, t_FP, t_FN, tH_TP, tH_TN, tH_FP, tH_FN, tE_TP, tE_TN, tE_FP, tE_FN, tC_TP, tC_TN, tC_FP, tC_FN,  h_h, h_e, h_c, e_h, e_e, e_c, c_h, c_e, c_c, sov_h, sov_e, sov_c, sov_o, flag,tH,tE,tC,tH_count,tE_count,tC_count = accuracy(
            x_1=y_test[0, :, 0].cpu(), x_2=y_test[0, :, 1].cpu(), x_3=y_test[0, :, 2].cpu(), label=test_label.cpu(),
            i=i, j=0, reallength1=reallength1t, epoch=epoch, who='test')

        hfn = hfn + tH_FN
        efn = efn + tE_FN
        cfn = cfn + tC_FN

        htp = htp + tH_TP
        etp = etp + tE_TP
        ctp = ctp + tC_TP

        htn = htn + tH_TN
        etn = etn + tE_TN
        ctn = ctn + tC_TN

        hfp = hfp + tH_FP
        efp = efp + tE_FP
        cfp = cfp + tC_FP

        H_H = H_H + h_h
        H_E = H_E + h_e
        H_C = H_C + h_c
        E_H = E_H + e_h
        E_E = E_E + e_e
        E_C = E_C + e_c
        C_H = C_H + c_h
        C_E = C_E + c_e
        C_C = C_C + c_c

        H=H+tH
        E = E + tE
        C = C + tC
        H_count = H_count + tH_count
        C_count = C_count + tC_count
        E_count = E_count + tE_count

        if (flag == 0):
            SOV_H = SOV_H + sov_h
            SOV_E = SOV_E + sov_e
            SOV_C = SOV_C + sov_c
            SOV = SOV + sov_o
        else:
            sov_count = sov_count - 1

            total = (TP + FN) * (TP + FP) * (TN + FN) * (TN + FP)
            h = (htp + hfn) * (htp + hfp) * (htn + hfn) * (htn + hfp)
            e = (etp + efn) * (etp + efp) * (etn + efn) * (etn + efp)
            c = (ctp + cfn) * (ctp + cfp) * (ctn + cfn) * (ctn + cfp)

        TP = TP + t_TP
        TN = TN + t_TN
        FP = FP + t_FP
        FN = FN + t_FN

    precision = TP / (TP + FP)

    HEC_acc = float(H + E + C) / float(H_count + E_count + C_count)

    print('HEC_acc:', HEC_acc)
    print('Precision', precision)

    print('H_H', H_H)
    print('H_E', H_E)
    print('H_C', H_C)
    print('E_H', E_H)
    print('E_E', E_E)
    print('E_C', E_C)
    print('C_H', C_H)
    print('C_E', C_E)
    print('C_C', C_C)

    print('SOV_H', SOV_H / sov_count)
    print('SOV_E', SOV_E / sov_count)
    print('SOV_C', SOV_C / sov_count)
    print('SOV', SOV / sov_count)
    print('SOV_count', sov_count)

    if (HEC_acc > h_acc):
        h_acc = HEC_acc
        h_sn = sn
        h_sp = sp
        h_mcc = mcc
        # torch.save(model.state_dict(), 'complex-1.25-msa-concat.model')

    return highest, BGRU, h_sn, h_sp, h_mcc, h_acc

high_acc = 0


def get_parameters(net):
    total_num = sum(p.numel() for p in net.parameters())
    trainable_num = sum(p.numel() for p in net.parameters() if p.requires_grad)
    print('Total', total_num, 'Trainable', trainable_num)


with torch.no_grad():
    high_acc_temp, bgru1, h_sn, h_sp, h_mcc, h_acc = save_model(high_acc=high_acc, epoch=0, bgru=bgru1,
                                                                h_sn=h_sn, h_sp=h_sp, h_mcc=h_mcc, h_acc=h_acc)

    high_acc = high_acc_temp
    # with torch.no_grad:
    #     for j in range(batchsize):
    #         accuracy(y_pred[j, :, 0].cpu(), y_pred[j, :, 1].cpu(), y_pred[j, :, 2].cpu(), i, j,
    #                  reallength1=reallength1, epoch=epoch)

print('Testing Finished!')
print('sn:', h_sn)
print('sp:', h_sp)
print('mcc:', h_mcc)
print('acc:', h_acc)
print('high_acc:', high_acc)

get_parameters(model)
