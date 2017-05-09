import sys
import random
import numpy as np
from scipy.sparse import csr_matrix
import argparse
import fw
import math

debug = False
model_name = ''
random_top = 9
noise_degree = 5
n_noise_observation = 1

VALID_MODEL = ['LinearRegression', 'LogisticRegression']

# Make relation between features and noise
def adapt_noise_fea(basic_fea, n_fea):
    for i in range(basic_fea.shape[1]):
        if i >= n_fea:
            basic_fea[0, i] = basic_fea[0, i-n_fea] ** 2
    return basic_fea

def gen_data(n_fea, n_sample, n_noise):
    basic_fea = np.random.randint(random_top, size=(1, n_fea+n_noise)) + 1
    if True:
        basic_fea = adapt_noise_fea(basic_fea, n_fea)
    noised_fea = np.asmatrix(basic_fea)
    fea = np.asmatrix(basic_fea[:, :n_fea])

    basic_x = np.random.randint(random_top, size=(n_sample, n_fea+n_noise)) + 1
    noised_x = np.asmatrix(basic_x)
    x = np.asmatrix(basic_x[:, :n_fea])
    noise = np.random.random(size=n_sample) * noise_degree

    y = fea * x.T
    # Adapt noise observation(Gaussian)
    for i in range(y.shape[1]):
        eps = np.random.randint(10)
        if eps < n_noise_observation:
            noise = np.random.normal(0, 1, 1)[0] # means and variances
            #noise = 1. * np.random.randint(1, 3) * y[0, i] / 10
            y[0, i] += noise
    return noised_fea, fea, noised_x, x, y

def print_gen_data(n_W, t_W, n_X, t_X, Y):
    nw_ptr = [str(x) for x in n_W.A.flatten()]
    tw_ptr = [str(x) for x in t_W.A.flatten()]
    y_ptr = [str(x) for x in Y.A.flatten()]

    print '\t\tnW:\t' + '\t'.join(nw_ptr)
    print '\t\ttW:\t' + '\t'.join(tw_ptr)
    print '\t\tY:\t' + '\t'.join(y_ptr)

    """
    print '='*10 + 'noised X' + '='*10
    for line in n_X.A:
        ptr = []
        for g in line:
            ptr.append(str(g))
        print '\t'.join(ptr)

    print '='*10 + 'true X' + '='*10
    for line in t_X.A:
        ptr = []
        for g in line:
            ptr.append(str(g))
        print '\t'.join(ptr)
    """

def succ_ratio(tgt_fea, trained_fea, n_fea):
    abs_tgt_fea = [abs(x) for x in tgt_fea]
    abs_trained_fea = [abs(x) for x in trained_fea]
    L = len(tgt_fea)
    fea_succ_ratio_1 = 0
    fea_succ_ratio_01 = 0
    fea_succ_ratio_001 = 0
    noise_succ_ratio_1 = 0
    noise_succ_ratio_01 = 0
    noise_succ_ratio_001 = 0
    for i in range(L):
        abs_tgt_feai = abs(tgt_fea[i])
        abs_trained_feai = abs(trained_fea[i])
        max_feai = abs_tgt_feai if abs_tgt_feai > abs_trained_feai else abs_trained_feai
        gap_fea = abs(tgt_fea[i] - trained_fea[i]) / max_feai
        if i < n_fea:
            if gap_fea < 0.1:
                fea_succ_ratio_1 += 1
            if gap_fea < 0.01:
                fea_succ_ratio_01 += 1
            if gap_fea < 0.001:
                fea_succ_ratio_001 += 1
        else:
            if gap_fea > 0.9:
                noise_succ_ratio_1 += 1
            if gap_fea > 0.99:
                noise_succ_ratio_01 += 1
            if gap_fea > 0.999:
                noise_succ_ratio_001 += 1
    L = 1. * L
    LF = 1. * n_fea
    LN = 1. * (L - n_fea)
    print '%lf\t%lf\t%lf\t%lf\t%lf\t%lf' % (fea_succ_ratio_1/LF, fea_succ_ratio_01/LF, fea_succ_ratio_001/LF, noise_succ_ratio_1/LN, noise_succ_ratio_01/LN, noise_succ_ratio_001/LN)

def build_and_fit(X, Y, W=None):
    if model_name == 0:
        from sklearn import linear_model
        model = linear_model.LinearRegression()
        model.fit(X, Y)
        return model
    elif model_name == 1:
        from sklearn.linear_model import LogistricRegression
        model = LogisticRegression(C=1.0, penalty='l1')
        model.fit(X, Y)
        return model
    # multi class
    elif model_name == 2:
        from sklearn import linear_model
        model = linear_model.LogisticRegression(C=1.0, multi_class='ovr', penalty='l2')
        model.fit(X, Y)
        return model
    elif model_name == 3:
        from sklearn.svm import SVC
        model = SVC()
        model.fit(X, Y)
        return model

def train(n_W, t_W, n_X, t_X, Y):
    from sklearn import linear_model
    X = np.asarray(n_X)
    Y = np.asarray(Y.A[0])
    model = build_and_fit(X, Y)

    if debug:
        print '\n\t\tmodel coefs', model.coef_
        print '\t\tmodel intercepts:', model.intercept_
    succ_ratio(n_W.A.flatten(), model.coef_, t_W.shape[1])

def mode_eva_data(args):
    def wifi_stat(wflist):
        pass

    def output_result(acc, ssum):
        pass

    def output_feature(model, dv):
        feature_names = dv.feature_names_
        coefs = model.coef_
        intercepts = model.intercept_
        for coef in coefs:
            ptr = []
            for idx in range(len(coef)):
                if coef[idx] == 0:
                    continue
                ptr.append(feature_names[idx] + ':' + str(coef[idx]))
            print '|'.join(ptr)

    from sklearn.feature_extraction import DictVectorizer
    from sklearn.model_selection import KFold
    dv = DictVectorizer()
    kf = KFold(n_splits=10, shuffle=True)
    wflist = []
    labels = []

    for line in fw.get_data(sys.stdin, '\t'):
        wf = line[0]
        label = line[1]
        wf = fw.str_to_wf(wf, normed=False)
        wflist.append(wf)
        labels.append(label)

    dv_wflist = dv.fit_transform(wflist)
    array_dv_wflist = dv_wflist.toarray()
    idx = 1
    train_acc_r_sum = 0
    test_acc_r_sum = 0
    for train, test in kf.split(wflist):
        train_X = [array_dv_wflist[i] for i in train]
        train_X = csr_matrix(train_X)
        train_Y = [labels[i] for i in train]
        train_Y = np.asarray(train_Y)

        test_X = [array_dv_wflist[i] for i in test]
        test_X = csr_matrix(test_X)
        test_Y = [labels[i] for i in test]
        test_Y = np.asarray(test_Y)

        #model = build_and_fit(train_X, train_Y)
        model = build_and_fit(train_X, train_Y)
        #debug = True
        if debug:
            output_feature(model, dv)
        #print model.predict(train_X)
        train_YY = model.predict(train_X)
        test_YY = model.predict(test_X)
        train_acc = 0
        test_acc = 0
        train_sum = 0
        test_sum = 0
        for i in range(train_Y.shape[0]):
            train_sum += 1
            if train_Y[i] == train_YY[i]:
                train_acc += 1
        for i in range(test_Y.shape[0]):
            test_sum += 1
            if test_Y[i] == test_YY[i]:
                test_acc += 1
        train_acc_ratio = 1. * train_acc / train_sum
        test_acc_ratio = 1. * test_acc / test_sum
        train_acc_r_sum += train_acc_ratio
        test_acc_r_sum += test_acc_ratio
        print 'Round %d: train:%lf(%d)\ttest:%lf(%d)' % (idx, train_acc_ratio, train_sum, test_acc_ratio, test_sum)
        idx += 1
    print 'Average train: %lf\t average test: %lf' % (train_acc_r_sum/idx, test_acc_r_sum/idx)

def mode_gen_data(args):
    range_fea = None
    range_sample = None
    range_noise = None

    if args.fea_range != None:
        range_fea = args.fea_range.split('-')
    if args.sample_range != None:
        range_sample = args.sample_range.split('-')
    if args.noise_range != None:
        range_noise = args.noise_range.split('-')
    n_fea = args.fea
    n_sample = args.sample
    n_noise = args.noise

    if range_fea != None:
        s, e = map(int, range_fea)
        for n_fea in range(s, e):
            sys.stdout.write('%d\t%d\t%d\t' % (n_fea, n_sample, n_noise))
            n_W,t_W, n_X, t_X, Y = gen_data(n_fea, n_sample, n_noise)
            train(n_W, t_W, n_X, t_X, Y)
            if debug:
                print_gen_data(n_W, t_W, n_X, t_X, Y)
    elif range_sample != None:
        s, e = map(int, range_sample)
        for n_sample in range(s, e):
            sys.stdout.write('%d\t%d\t%d\t' % (n_fea, n_sample, n_noise))
            n_W,t_W, n_X, t_X, Y = gen_data(n_fea, n_sample, n_noise)
            train(n_W, t_W, n_X, t_X, Y)
            if debug:
                print_gen_data(n_W, t_W, n_X, t_X, Y)
    elif range_noise != None:
        s, e = map(int, range_noise)
        for n_noise in range(s, e):
            sys.stdout.write('%d\t%d\t%d\t' % (n_fea, n_sample, n_noise))
            n_W,t_W, n_X, t_X, Y = gen_data(n_fea, n_sample, n_noise)
            train(n_W, t_W, n_X, t_X, Y)
            if debug:
                print_gen_data(n_W, t_W, n_X, t_X, Y)
    else:
        sys.stdout.write('%d\t%d\t%d\t' % (n_fea, n_sample, n_noise))
        n_W, t_W, n_X, t_X, Y = gen_data(n_fea, n_sample, n_noise)
        train(n_W, t_W, n_X, t_X, Y)
        if debug:
            print_gen_data(n_W, t_W, n_X, t_X, Y)

def mode_stat_data(args):
    def cal_means_vars(data):
        ret_value = {}
        for k, v in data.items():
            ssum = sum(v)
            L = len(v)
            means = ssum/L
            variance = 0
            for vv in v:
                variance += (means - vv)**2
            variance = 1. * math.sqrt(variance) / L
            ret_value[k] = [means, variance]
        return ret_value

    def sort_data(wflist):
        pass

    wflist = {}
    wf_means_vars = {}

    for line in fw.get_data(sys.stdin, '\t'):
        wfs = line[0].split('|')
        tgt = line[1]
        if tgt not in wflist:
            wflist[tgt] = {}
        for wf in wfs:
            wf = wf.split(';')
            if len(wf) != 3:
                continue
            ap, ssid, sig = wf
            ap = ap.replace(':', '')
            sig = int(sig)
            if ap in wflist[tgt]:
                wflist[tgt][ap].append(sig)
            else:
                wflist[tgt][ap] = [sig]
    #print wflist
    for k, v in wflist.items():
        print k, cal_means_vars(v)


def main():
    argsparser =  argparse.ArgumentParser()

    argsparser.add_argument('-m', '--mode', type=int, help='Mode\
            \t1.generate the data\
            \t2.Evaulate real data by model\
            \t3.Evaulate the real data by statical analysis')

    argsparser.add_argument('-f', '--fea', type=int, help='number of features', default=3)
    argsparser.add_argument('-s', '--sample', type=int, help='number of samples', default=2)
    argsparser.add_argument('-n', '--noise', type=int, help='number of noise', default=1)
    argsparser.add_argument('-d', '--debug', type=bool, help='debug mode', default=False)
    argsparser.add_argument('-fr', '--fea_range', type=str, help='range of features[1-100]')
    argsparser.add_argument('-sr', '--sample_range', type=str, help='range of samples[1-100]')
    argsparser.add_argument('-nr', '--noise_range', type=str, help='range of noise[1-100]')
    argsparser.add_argument('-na', '--model_name', type=int, help='Model\
            \t0.LinearRegression\
            \t1.LogisticRegression', default=0)

    args = argsparser.parse_args()

    global debug, model_name
    mode = args.mode
    model_name = args.model_name
    debug = args.debug

    if mode == 1:
        mode_gen_data(args)
    elif mode == 2:
        mode_eva_data(args)
    elif mode == 3:
        mode_stat_data(args)
    else:
        print 'Pick the mode[-m]\t1.gen data\t2.Eva real data'

if __name__ == '__main__':
    main()
