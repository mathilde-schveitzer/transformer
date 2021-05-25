import os
import numpy as np
import math
import torch
import time
import random
import torch.nn as nn
import torch.nn.functional as F
import load_data as ld

class TransformerModel(nn.Module):

    def __init__(self, ninp, nhead, nhid, nlayers, backast_size, forecast_size, dropout=0.5, device=torch.device('cpu')):
        super(TransformerModel, self).__init__()
        from torch.nn import TransformerEncoder, TransformerEncoderLayer
        self.model_type = 'Transformer'
        self.embed_dims=ninp*nhead
        self.device = device
        encoder_layers = TransformerEncoderLayer(self.embed_dims, nhead, nhid, dropout, activation='gelu')

        self.encoder=nn.Linear(ninp, self.embed_dims)
        self.transformer_encoder = TransformerEncoder(encoder_layers, nlayers)       
        self.decoder=Decoder(self.embed_dims, ninp, forecast_size,backast_size,device=device)


        self.parameters = []
        self.parameters = nn.ParameterList(self.parameters)
        
        self.optimizer=torch.optim.Adam(self.parameters(),lr=1e-3,betas=(0.9,0.98))
        self._loss=F.l1_loss

        self.to(self.device)
        
        print('|T R A N S F O R M E R : Optimus Prime is ready |')

    def forward(self, input):
        input=input.to(self.device)
        
        input = self.encoder(input)

        output = self.transformer_encoder(input)

        _output = self.decoder(output)

        return _output
    
    def do_training(self,xtrain,ytrain):
        self.train() # Turn on the train mode (herited from module)
        total_loss = 0.
        start_time = time.time()

        assert len(xtrain)==len(ytrain)

        shuffled_indices=list(range(len(xtrain)))
        random.shuffle(shuffled_indices)
        
        for k,batch_id in enumerate(shuffled_indices):
           
            data, targets = xtrain[batch_id], ytrain[batch_id]
            data=data.transpose(0,1)
            
            self.optimizer.zero_grad()
            output = self(data)
            
            loss=self._loss(output.reshape(-1), targets.transpose(0,1).reshape(-1).to(self.device))
                        
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.parameters(), 0.5)
            self.optimizer.step()

            total_loss += loss.item()
            print('----------- total loss :', loss.item())
            log_interval = 1
            if k % log_interval == 50 : # donc tous les "log_interval" batchs
                cur_loss = total_loss / log_interval
                elapsed = time.time() - start_time
                print(' {:5d}/{:5d} batches | ms/batch {:5.2f} | ''loss {:5.2f}' .format(batch_id, len(xtrain),elapsed * 1000 / log_interval,cur_loss))
        
                start_time = time.time()
                total_loss=0

    def evaluate(self, xtest, ytest, bsz, val, name, predict=False, verbose=False):  
        self.eval() # Turn on the evaluation mode (herited from module)

        def split(arr, size):
           arrays = []
           while len(arr) > size:
               slice_ = arr[:size]
               arrays.append(slice_)
               arr = arr[size:]
           arrays.append(arr)
           return arrays
       
        xtest_list=split(xtest, bsz)
        ytest_list=split(ytest,bsz)
        assert len(xtest_list)==len(ytest_list)

        if verbose :
           if val :
               print('---VAL---')
       
           else :
               print('---PAVAL---')
       
        if predict :
            prediction=torch.zeros_like(ytest)
            
        test_loss = []
        
        for batch_id in range(0, len(xtest_list)):
       
            data,targets=xtest_list[batch_id],ytest_list[batch_id]
            data=data.transpose(0,1)
            output=self(data)
            loss=self._loss(output.reshape(-1),targets.transpose(0,1).reshape(-1).to(self.device)).item()

            test_loss.append(loss)

            if predict :
                #d'ou l'importance de passer les batch dans l'ordre
                
                
                output=output.transpose(0,1)
                
                prediction[batch_id*output.shape[0]:(batch_id+1)*output.shape[0],:,:]=output
                
                print(prediction)
        mean_loss=np.mean(test_loss)

        if val :
            print(f'Validation loss : {mean_loss:.4f}')
        else :
            print(f'Training loss : {mean_loss :.4f}')
            
        if predict :
            if val :
                print('-------we save test values----------')
                torch.save(prediction,'./data/{}/predictions_test.pt'.format(name))
            else :
                print('-------we save train values ------')
                torch.save(prediction, './data/{}/predictions_train.pt'.format(name))
        return(mean_loss)


    def fit(self, xtrain, ytrain, xtest, ytest, bsz, eval_bsz, epochs, filename, save=True, verbose=False):
        store_val_loss=np.zeros(epochs)
        store_loss=np.zeros(epochs)

        def split(arr, size):
            arrays = []
            while len(arr) > size:
                slice_ = arr[:size]
                arrays.append(slice_)
                arr = arr[size:]
            arrays.append(arr)
            return arrays
            
        for epoch in range(1, epochs + 1):
            epoch_start_time = time.time()
            xtrain_list=split(xtrain, bsz)
            ytrain_list=split(ytrain, bsz)

            self.do_training(xtrain_list,ytrain_list)
           
            val_loss = self.evaluate(xtest, ytest, eval_bsz, True, filename, predict=False, verbose=verbose)
            train_loss = self.evaluate(xtrain, ytrain, bsz, False, filename, predict=False,verbose=verbose)

            store_loss[epoch-1]=train_loss
            store_val_loss[epoch-1]=val_loss

        if save :
            np.savetxt('./data/{}/train_loss.txt'.format(filename), store_loss)
            np.savetxt('./data/{}/val_loss.txt'.format(filename), store_val_loss)



class MLForecast(nn.Module) :
    def __init__(self, forecast_size, backast_size, device='cpu') :
        super(MLForecast, self).__init__()
        self.MLP=nn.Linear(backast_size, forecast_size)
        self.to(device)

    def forward(self, x):
        input=x.transpose(0,2) # "[forecast_size][batch][ninp] => [ninp][batch][forecast_size]"
        output=self.MLP(x)
        return(output)

class Decoder(nn.Module) :
    def __init__(self, ninp, nout, forecast_size, backast_size, device='cpu') :
       super(Decoder, self).__init__()
       self.MLP=nn.Linear(ninp, nout)
       self.MLF=nn.Linear(backast_size,forecast_size)
       self.to(device)

    def forward(self,x,verbose=False):
        x=self.MLP(x)
        if verbose :
            print('encoder input :', x.shape)
        output=self.MLF(x.transpose(0,2))
        if verbose :
            print('encoder output :', output.shape)            
        return(output.transpose(0,2))
