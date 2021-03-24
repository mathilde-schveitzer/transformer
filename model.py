import os
import numpy as np
import math
import torch
import time
import torch.nn as nn
import torch.nn.functional as F
import load_data as ld

class TransformerModel(nn.Module):

    def __init__(self, ntoken, ninp, nhead, nhid, nlayers, bptt, learning_rate=1e-5, dropout=0.5, device=torch.device('cpu')):
        super(TransformerModel, self).__init__()
        from torch.nn import TransformerEncoder, TransformerEncoderLayer
     #   self.ntokens=ntoken
        self.model_type = 'Transformer'
        self.embed_dims=ninp*nhead
        self.device = device
     #   self.embed_dims=6
     #   self.pos_encoder = PositionalEncoding(self.embed_dims, dropout)
        encoder_layers = TransformerEncoderLayer(self.embed_dims, nhead, nhid, dropout, activation='gelu')
        self.transformer_encoder = TransformerEncoder(encoder_layers, nlayers)
        self.encoder=MLP(ninp,self.embed_dims,3,124,device=self.device)
        self.decoder=MLP(nhead,1,3,124,device=self.device)
        self.to(self.device)
        self.bptt = bptt
#        self.criterion=None
        self.parameters = []
        self.parameters = nn.ParameterList(self.parameters)
        self.optimizer=torch.optim.SGD(params=self.parameters(), lr=1e-2)
#        self.optimizer=torch.optim.Adam(lr=1e-2, params=self.parameters())
        self.scheduler=None
        self._loss=F.mse_loss
        self.init_weights()
        print('|T R A N S F O R M E R : Optimus Prime is ready |')
        
    # def generate_square_subsequent_mask(self, sz):
    #     mask = (torch.triu(torch.ones(sz, sz)) == 1).transpose(0, 1)
    #     mask = mask.float().masked_fill(mask == 0, float('-inf')).masked_fill(mask == 1, float(0.0))
    #     return mask

    def init_weights(self):
        initrange = 0.1
    #     self.encoder.weight.data.uniform_(-initrange, initrange)
    #     self.decoder.bias.data.zero_()
    #     self.decoder.weight.data.uniform_(-initrange, initrange)

    def forward(self, input):
        _input = self.encoder(input).to(self.device)
        output = self.transformer_encoder(_input).to(self.device)
        _output = self.decoder(output).to(self.device)
        return _output
    
    def do_training(self,train_data):
        self.train() # Turn on the train mode (herited from module)
        total_loss = 0.
        start_time = time.time()
      #  src_mask = self.generate_square_subsequent_mask(self.bptt).to(self.device)
        for batch, i in enumerate(range(0, train_data.size(0) - 1, self.bptt)):
            data, targets = ld.get_batch(train_data, i, self.bptt)
            data=data.to(self.device)
            targets=targets.to(self.device)
            self.optimizer.zero_grad()
            output = self(data)
            output=ld.flatten(output)
            loss=self._loss(output, targets)
           # loss = self.criterion(output.view(-1, self.ntokens), targets)
            loss.backward()
          #  torch.nn.utils.clip_grad_norm_(self.parameters(), 0.5)
            self.optimizer.step()

            total_loss += loss.item()
            log_interval = 200
            if batch % log_interval == 0 and batch > 0:
                cur_loss = total_loss / log_interval
                elapsed = time.time() - start_time
                print('| epoch {:3d} | {:5d}/{:5d} batches | ms/batch {:5.2f} | '
                      'loss {:5.2f} | ppl {:8.2f}'.format(
                          epoch, batch, len(train_data) // self.bptt,
                          elapsed * 1000 / log_interval,
                          cur_loss, math.exp(cur_loss)))
                total_loss = 0
                start_time = time.time()

    def evaluate(self, data_source, val):  
        self.eval() # Turn on the evaluation mode (herited from module)
        test_loss = []
        for i in range(0, data_source.size(0)-1, self.bptt):
            data,targets=ld.get_batch(data_source, i, self.bptt)
            output=self(data).to(self.device)
            _loss=self._loss(ld.flatten(output).to(self.device),targets.to(self.device)).item()
            test_loss.append(_loss)
        mean_loss=np.mean(test_loss)
        if val :
            print(f'Validation loss : {mean_loss:.4f}')
        else :
            print(f'Train loss : {mean_loss:.4f}')
        return(mean_loss)


    def fit(self, train_data, val_data, epochs, filename):
        store_val_loss=np.zeros(epochs)
        store_loss=np.zeros(epochs)

        self.scheduler=torch.optim.lr_scheduler.StepLR(self.optimizer, step_size=500, gamma=0.1)
       

        for epoch in range(1, epochs + 1):
            epoch_start_time = time.time()
           
            self.do_training(train_data)
           
            val_loss = self.evaluate(val_data, val=True)
            train_loss = self.evaluate(train_data, val=False)
            store_loss[epoch-1]=train_loss
            store_val_loss[epoch-1]=val_loss
            
            print('-' * 89)
            print('''| epoch {:3d} | time: {:5.2f}s | valid loss {:5.2f} | train loss {:5.2f} |
                  valid ppl {:8.2f}'''.format(epoch, (time.time() - epoch_start_time), 
                                             val_loss, train_loss, math.exp(val_loss)))
            print('-' * 89)
            self.scheduler.step()
       
        np.savetxt('./data/{}/train_loss.txt'.format(filename), store_loss)
        np.savetxt('./data/{}/val_loss.txt'.format(filename), store_val_loss)

class PositionalEncoding(nn.Module):

    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)


class MLP(nn.Module):
    def __init__(self, input_size, output_size, nhidden, dim_hidd, device):
        super(MLP, self).__init__()
        self.input_size=input_size
        self.output_size=output_size
        self.fc_layers=[]
        self.fc_layers.append(nn.Linear(self.input_size, dim_hidd).to(device))
        for k in range(nhidden):
            self.fc_layers.append(nn.Linear(dim_hidd, dim_hidd).to(device))
        self.fc_layers.append(nn.Linear(dim_hidd, self.output_size).to(device))
        self.device=device
        self.to(device)
        
    def forward(self,x):
        output=x
        for f in self.fc_layers :
            output=f(output)
        return(output) 
