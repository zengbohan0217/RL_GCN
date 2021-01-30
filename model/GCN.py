import torch
import torch.nn as nn
import torch.nn.init as init
import torch.nn.functional as F

DEVICE = torch.device('cuda')

class GCNconv(nn.Module):
    def __init__(self, in_c, out_c, bais=False):
        super().__init__()
        self.bais = bais
        self.W = nn.Parameter(torch.FloatTensor(in_c, out_c))
        init.xavier_uniform_(self.W, gain=1.44)
        if self.bais:
            self.B = nn.Parameter(torch.FloatTensor(1, out_c))
            init.normal(self.B)

    def forward(self, g_data, g_adj):
        N = g_adj.size(0)  # N,N
        B = g_data.size(0)  # B,N,F
        # A\hat=A+I
        g_adj = g_adj + torch.eye(N).to(DEVICE)
        # D\hat^(-1/2)
        degree = torch.diag(g_adj.sum(dim=1)) ** (-1 / 2)
        # 0的-1/2要手动处理一下。
        degree[degree == float("inf")] = 0
        out = torch.mm(degree, g_adj)
        out = torch.mm(out, degree)  # N,N
        # matmul 可以自动扩展矩阵乘法。如下所示
        out = torch.matmul(out, g_data)  # [N,N]*[B,N,in_C] =[B,N,int_c]
        out = torch.matmul(out, self.W)  # [B,N,int_]*[int_c,out_c] =[B,N,out_c]
        if self.bais:
            out = out + self.B
        return out

class GCNnet(nn.Module):
    def __init__(self, in_c, hid_c, out_c, bais=False):
        super().__init__()
        self.conv1 = GCNconv(in_c, hid_c, bais=bais)
        self.conv2 = GCNconv(hid_c, out_c, bais=bais)

        self.act = nn.ReLU()

    def forward(self, graph, flow_data):
        """
        :param graph: tensor[N*N]
        :param flow_data: tensor[batch_size * N * feature_size]
        :param device:
        :return:
        """
        graph = graph[0]  # [N,N]
        flow_x = flow_data  # [B,N,D,H] 四个维度分别为： batch 节点 节点特征维度  H=1
        B, N = flow_x.size(0), flow_x.size(1)
        flow_x = flow_x.view(B, N, -1)  # [B, N, H*D]
        out1 = self.conv1(flow_x, graph)
        print(out1.device)
        out2 = self.conv2(out1, graph)
        return out2.unsqueeze(2)  # [B,N,1,1]