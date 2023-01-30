
import pandas as pd

class ConfusionMatrix:

    def __init__(self,df=None):
        self.TP = 0
        self.FP = 0
        self.FN = 0
        self.TN = 0
        if df is not None:
            matrix=self.getMatrix(df)
            self.TP = matrix.TP
            self.FP = matrix.FP
            self.FN = matrix.FN
            self.TN = matrix.TN

    def getMatrix(self,df):
        matrix=ConfusionMatrix()
        for _,row in df.iterrows():
            ## 0 is with mask, 1 is no mask
            predict,label=row
            if(label=="with_mask"):
                if(predict==label):
                    matrix.TP+=1
                else:
                    matrix.FN+=1
            else:
                if (predict==label):
                    matrix.TN+=1
                else:
                    matrix.FP+=1
        return matrix

    def Precision(self):
        try:
            return self.TP/(self.TP+self.FP)
        except:
            return 0

    def Recall(self):
        try:
            return self.TP/(self.TP+self.FN)
        except:
            return 0

    def Accuracy(self):
        try:
            return (self.TP+self.TN)/(self.TP+self.FP+self.TN+self.FN)
        except:
            return 0

    def F1_core(self):
        recall=self.Recall()
        precision=self.Precision()
        try:
            return 2*precision*recall/(precision+recall)
        except:
            return 0
    
    def allScore(self):
        accuracy=self.Accuracy()
        recall=self.Recall()
        precision=self.Precision()
        f1_score=self.F1_core()
        return accuracy,recall,precision,f1_score