import sys
import os
import time
import argparse
import torch
from nbeats import *

def main(data_name,storage,ninp,device='cpu'):

# create a list containing the names of the models :
    
    name_NBTR='nbeats_fc_vs_{}'.format(storage)
#    name_NBFC='nbeats_tr_vs_{}'.format(storage)
    name_TR='transformer_mlp_{}'.format(storage)
#    name_TRT2V='transformer_t2v_{}'.format(storage)
    names=[name_NBTR, name_TR]
#    names=[name_NBTR,name_NBFC,name_TR,name_TRT2V]

# create the directory in which the results will be saved :
    
    storage_paths=['./data/{}'.format(name) for name in names]

    for k in range(len(storage_paths)) :
        if not os.path.exists(storage_paths[k]) :
            os.makedirs(storage_paths[k])

    xtrain=torch.load('./data/{}/xtrain.pt'.format(data_name))
    ytrain=torch.load('./data/{}/ytrain.pt'.format(data_name))
    xtest=torch.load('./data/{}/xtest.pt'.format(data_name))
    ytest=torch.load('./data/{}/ytest.pt'.format(data_name))

# hyperparameters fixed for training session :

    epochs=400
    bsz=50
    eval_bsz=50
    backcast_length=100 #to choose according to the set of data loaded above
    forecast_length=100

    ninp+=1

# creating the models
    models=[]
    model=None
    
    model=NBeatsNet(ninp, device=device, forecast_length=forecast_length, backcast_length=backcast_length, block_type='fully_connected')
    models.append(model)
 #   model=NBeatsNet(ninp, device=device, forecast_length=forecast_length, backcast_length=backcast_length, block_type='Tr')
 #   models.append(model)
    model=TransformerModel(ninp, nhead=4, nhid=64, nlayers=2, backast_size=backcast_length, forecast_size=forecast_length, dropout=0.1, t2v=False, device=device)
    models.append(model)
 #   model=TransformerModel(ninp, nhead=4, nhid=64, nlayers=2, backast_size=backcast_length, forecast_size=forecast_length, dropout=0.1, t2v=True, device=device)
 #   models.append(model)
    
    for x in models :
        print("Model structure: ", x, "\n\n")
    
# training the NBeats models :
    for k in range(1):
         models[k].fit(xtrain[:,:,:ninp], ytrain[:,:,:ninp], xtest[:,:,:ninp], ytest[:,:,:ninp], names[k], epochs=epochs, batch_size=bsz)

# # training Transformer models :
    for k in range(1,len(models)):
         models[k].fit(xtrain[:,:,:ninp], ytrain[:,:,:ninp], xtest[:,:,:ninp], ytest[:,:,:ninp], bsz, epochs, names[k])

#    for k in range(0,len(models)):
#         models[k].fit(xtrain[:,:,:ninp], ytrain[:,:,:ninp], xtest[:,:,:ninp], ytest[:,:,:ninp], bsz, epochs, names[k])

# comment this part if you're not interested in visualizing what are the different models able to predict

# load data a second time since they have been modified by the shuffled methods called in fit (annoying when reconstituting the whole signal)
    xtrain=torch.load('./data/{}/xtrain.pt'.format(data_name))
    ytrain=torch.load('./data/{}/ytrain.pt'.format(data_name))
    xtest=torch.load('./data/{}/xtest.pt'.format(data_name))
    ytest=torch.load('./data/{}/ytest.pt'.format(data_name))
    x_train=xtrain[:,:,:ninp]
    y_train=ytrain[:,:,:ninp]
    x_test=xtest[:,:,:ninp]
    y_test=ytest[:,:,:ninp]
    
    for k in range(len(models)):
        test_loss = models[k].evaluate(x_test, y_test, eval_bsz, names[k], False, predict=True)
        train_loss = models[k].evaluate(x_test, y_test, eval_bsz, names[k], True, predict=True)

    
if __name__ == '__main__':
   parser=argparse.ArgumentParser()
   parser.add_argument('data', help='The name of the folder in which you want to load the data from')
   parser.add_argument('storage', help='The name of the folder in which out data will be saved')
   parser.add_argument('ninp', help='number of input signals')
   parser.add_argument('-device', help='Processor used for torch')
   args=parser.parse_args()
   if args.device :
       main(args.data, args.storage, int(args.ninp), device=args.device)
   else :
       main(args.data, args.storage, int(args.ninp))

    
