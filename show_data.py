import sys
import numpy as np
import matplotlib.pyplot as plt
import argparse
import torch
import random
from load_data import merge_data, merge_line

def main(signal, datatype, dim=[], test=False, signal2=''):

    fig=plt.figure()

    if datatype=='loss':
        for k,signal in enumerate(signals) :
            train_pass='./data/{}/train_loss.txt'.format(signal)
            val_pass='./data/{}/val_loss.txt'.format(signal)
            numpy_train=np.loadtxt(train_pass)
            numpy_val=np.loadtxt(val_pass)
#            plt.plot(numpy_val,label= 'Erreur sur le validation test : {}'.format(signal))
            if k==0 : plt.plot(numpy_val, label='Erreur sur le validation test : Nbeats ')
            if k==1 : plt.plot(numpy_val, label='Erreur sur le validation test : Transformer')
            if k==2 : plt.plot(numpy_val, label='Erreur sur le validation test : nhidd=128')
            if k==3 : plt.plot(numpy_val, label='Erreur sur le validation test : nhidd=256')
            
    if datatype=='pos_encod':
        name=signal+'_encod'
        name_=signal+'2'
        
        train_pass='./data/{}/train_loss.txt'.format(name)
        val_pass='./data/{}/val_loss.txt'.format(name)
        numpy_train=np.loadtxt(train_pass)
        numpy_val=np.loadtxt(val_pass)
        plt.plot(numpy_train,label= 'Erreur sur le training test - with pos encoding')
        plt.plot(numpy_val, label='Erreur sur le validation test - with pos encoding')
        
        train_pass2='./data/{}/train_loss.txt'.format(name_)
        val_pass2='./data/{}/val_loss.txt'.format(name_)
        numpy_train_=np.loadtxt(train_pass2)
        numpy_val_=np.loadtxt(val_pass2)
        plt.plot(numpy_train_,label= 'Erreur sur le training test - without  pos encoding')
        plt.plot(numpy_val_, label='Erreur sur le validation test - without pos encoding')

    if datatype=='prediction':

        predictions=[]
        for i in range(1,len(signal)):
            predict_path='./data/{}/predictions_train.pt'.format(signal[i])
            prediction=torch.load(predict_path,map_location=torch.device('cpu')) # [nb]x[forecast_size]x[dim]
            predictions.append(prediction)
            
        xtrain_path='./data/{}/xtest.pt'.format(signal[0])
        ytrain_path='./data/{}/ytest.pt'.format(signal[0])
        data=torch.load(xtrain_path, map_location=torch.device('cpu'))
        target=torch.load(ytrain_path, map_location=torch.device('cpu'))

        k=random.randrange(prediction.shape[0])
        #k=2
        print(k)
        for x,prediction in enumerate(predictions) :
            for i in dim :
                to_predict=prediction[:,:,i]
                converted_data=data[:,:,i]
                converted_target=target[:,:,i]
            if x==0 :
                plt.plot(merge_line(converted_data,to_predict,k),label='predicted with Nbeats')
                plt.plot(merge_line(converted_data,converted_target,k),label='target')
            if x==1 :
                plt.plot(merge_line(converted_data, to_predict, k), label='predicted with Transformer')

                
    if datatype=='whole_prediction':
        predict_path='./data/{}/predictions_whole_train_set.pt'.format(signal)
        data_train_set_path='./data/{}/data_train_set.txt'.format(signal)
        get_data_train_path='./data/{}/get_train_data_for_predict.pt'.format(signal)
        
        get_data_train=torch.load(get_data_train_path, map_location=torch.device('cpu'))
        data_train_set=np.loadtxt(data_train_set_path)
        prediction_set=torch.load(predict_path, map_location=torch.device('cpu'))

        plt.plot(data_train_set[0,:], label='before get_data 0')
        for k in range(4) : # should be < than nlimit chosen in kratos_trainer.py
            get_data=get_data_train[:,:,k].reshape(-1).numpy()
            plt.plot(get_data, label='after get_data # {}'.format(k))
            get_output=prediction_set[:,:,k].reshape(-1).detach().numpy()
            plt.plot(get_output,label='predicted data # {}'.format(k))
            

    plt.legend()
    plt.show()

        
if __name__ == '__main__' :

    parser=argparse.ArgumentParser()
    parser.add_argument('name', help='Name of the signal analyzed')
    parser.add_argument('data_type', help='Precise what you want to show (options : loss)')
    parser.add_argument('-dimension', help='List of dim you wanna plot, example : 1,2,3 ')
    parser.add_argument('-test', help='set to true if you want to analyse the testing set (default training set)')
    parser.add_argument('-name2', help='If you want to compare two different signals')
    parser.add_argument('-name3', help='If you want to compare three different signals')
    parser.add_argument('-name4', help='If you want to compare four different signals (loss only)')
    args=parser.parse_args()

    def to_list(blabla) :
        return([int(s) for s in blabla if s!=','])
    if args.data_type=='loss' :
        signals=[]
        signals.append(args.name)   
        if args.name2 :
            signals.append(args.name2)
            if args.name3 :
                signals.append(args.name3)
                if args.name4 :
                    signals.append(args.name4)
        main(signals, args.data_type)
    if args.data_type=='prediction' :
        signals=[]
        signals.append(args.name)   
        if args.name2 :
            signals.append(args.name2)
            if args.name3 :
                signals.append(args.name3)
                if args.name4 :
                    signals.append(args.name4)
        main(signals, args.data_type, dim=to_list(args.dimension))
    if args.dimension :
        if args.test :
            if args.name2 :
                main(args.name, args.data_type, dim=to_list(args.dimension),test=True,signal2=args.name2)
            else :
                main(args.name, args.data_type, dim=to_list(args.dimension),test=True)
        else :
            if args.name2 :
                main(args.name, args.data_type, dim=to_list(args.dimension),signal2=args.name2)
            else :
                main(args.name, args.data_type, dim=to_list(args.dimension))
    else :
         if args.test :
            if args.name2 :
                main(args.name, args.data_type,test=True,signal2=args.name2)
            else :
                main(args.name, args.data_type,test=True)
         else :
            if args.name2 :
                main(args.name, args.data_type,signal2=args.name2)
            else :
                main(args.name, args.data_type)
    
    
