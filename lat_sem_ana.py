import numpy as np
import cPickle as pkl
from sklearn.decomposition import TruncatedSVD
from nlputils.features import FeatureTransform, features2mat
from nlputils.dict_utils import norm_dict
from plot_utils import plot_score_distr, calc_simcoef_distr, group_combis, calc_auc, make_combis
'''
# wichtig: max renorm!
ft = FeatureTransform(renorm='max')
docfeats = ft.texts2features(textdict)
doc_ids = docfeats.keys()
# transform features into matrix
print "transforming features into matrix"
X, _ = features2mat(docfeats, train_ids)
print "performing LSA - explained variance:",
svd = TruncatedSVD(n_components=1000, n_iter=7, random_state=42)
X = svd.fit_transform(X)
print svd.explained_variance_ratio_.sum()
print "computing cosine similarity"
xnorm = np.linalg.norm(X, axis=1)
X /= xnorm.reshape(X.shape[0], 1)
S = X.dot(X.T)
'''

def make_svd_feats():
    target_ids = np.load('../corpus/target_ids.npy')
    random_ids = np.load('../corpus/random_ids.npy')
    dupl_ids = np.load('../corpus/dupl_ids.npy').item()
    cited_ids = np.load('../corpus/cited_ids.npy').item()
    id_dict = make_combis(target_ids, random_ids, cited_ids, dupl_ids)
 
    # load corpus
    pat_corpus = np.load('../corpus/corpus_claims.npy').item()
    # extract features
    ft = FeatureTransform(renorm='max')
    docfeats = ft.texts2features(pat_corpus)
    doc_ids = docfeats.keys()
    # split into target and rest
    train_feats = {pid : pat for pid, pat in docfeats.items() if pid not in target_ids}
    target_feats = {pid : docfeats[pid] for pid in target_ids}
    #np.save('human_eval/corpus_info/train_feats_claims.npy', train_feats)
    #np.save('human_eval/corpus_info/target_feats_claims.npy', target_feats)
    return train_feats, target_feats

def apply_lsa_rel_corpus():
    # load combis for small corpus
    combis = np.load('human_eval/corpus_info/combis.npy')
    target_ids = list(set([comb[0] for comb in combis]))
    single_pat_corpus = np.load('human_eval/corpus_info/single_pat_corpus.npy').item()
    ft = FeatureTransform(renorm='max')
    docfeats = ft.texts2features(single_pat_corpus)
    doc_ids = docfeats.keys()
    train_feats = {pid : pat for pid, pat in docfeats.items() if pid not in target_ids}
    target_feats = {pid : docfeats[pid] for pid in target_ids}
    # make feature matrices
    X_train, featurenames = features2mat(train_feats, train_feats.keys())
    X_target, _ = features2mat(target_feats, target_feats.keys(), featurenames)
    # train on full patent corpus (excluding target patents)
    svd = TruncatedSVD(n_components=100, n_iter=7, random_state=42)
    X_train_svd = svd.fit_transform(X_train)
    # make feat mat for small corpus
    X_target_svd = svd.transform(X_target)
    patfeats_lsa = {pid: norm_dict(dict(zip(range(100), X_train_svd[i,:])), 'length') for i, pid in enumerate(train_feats.keys())}
    for i, pid in enumerate(target_feats.keys()):
        patfeats_lsa[pid] = norm_dict(dict(zip(range(100), X_target_svd[i,:])), 'length')
    pat_ids = np.load('human_eval/corpus_info/pat_ids.npy')
    binary_label_pairs = np.load('human_eval/corpus_info/binary_label_pairs.npy').item()
    human_label_pairs = np.load('human_eval/corpus_info/human_label_pairs.npy').item()
    binary_sim_combis, binary_diff_combis = group_combis(binary_label_pairs)
    human_sim_combis, human_diff_combis = group_combis(human_label_pairs)
    for simcoef in ['linear']:
        binary_scores = calc_simcoef_distr(patfeats_lsa, ['random', 'cited'], 
                                           {'cited': binary_sim_combis, 'random': binary_diff_combis},
                                           simcoef)
        human_scores = calc_simcoef_distr(patfeats_lsa, ['irrelevant', 'relevant'],
                                          {'relevant': human_sim_combis, 'irrelevant': human_diff_combis},
                                          simcoef)
        binary_auc = calc_auc(binary_scores['cited'], binary_scores['random'])[2]
        human_auc = calc_auc(human_scores['relevant'], human_scores['irrelevant'])[2]
        plot_score_distr('human_eval', simcoef, ['random', 'cited'], 
                         {'cited': binary_scores['cited'], 'random': binary_scores['random']},
                         binary_auc, ['cited'], histdir='lsa_full250_rel_corp', bins=20)
        plot_score_distr('human_eval', simcoef, ['irrelevant', 'relevant'], 
                 {'relevant': human_scores['relevant'], 'irrelevant': human_scores['irrelevant']},
                 human_auc, ['relevant'], histdir='lsa_full250_rel_corp', bins=20)

if __name__ == "__main__":
    apply_lsa_rel_corpus()
    '''
    train_feats, target_feats = make_svd_feats()
    target_ids = np.load('../corpus/target_ids.npy')
    random_ids = np.load('../corpus/random_ids.npy')
    dupl_ids = np.load('../corpus/dupl_ids.npy').item()
    cited_ids = np.load('../corpus/cited_ids.npy').item()

    id_dict = make_combis(target_ids, random_ids, cited_ids, dupl_ids)
    #train_feats = np.load('human_eval/corpus_info/train_feats.npy').item()
    #target_feats = np.load('human_eval/corpus_info/target_feats.npy').item()
    # make feature matrices
    X_train, featurenames = features2mat(train_feats, train_feats.keys())
    np.save('human_eval/corpus_info/featurenames_claims.npy', featurenames)
    X_target, _ = features2mat(target_feats, target_feats.keys(), featurenames)
    for n_comp in [100, 250, 500, 1000]:
        print n_comp
        # fit LSA
        svd = TruncatedSVD(n_components=n_comp, n_iter=7, random_state=42)
        X_train_svd = svd.fit_transform(X_train)
        #pkl.dump(svd, open('human_eval/models/svd_%i.model' %n_comp, 'wb'), -1)
        X_target_svd = svd.transform(X_target)
        svd_feats = {pid: norm_dict(dict(zip(range(n_comp), X_train_svd[i,:])), 'length') for i, pid in enumerate(train_feats.keys())}
        for i, pid in enumerate(target_feats.keys()):
            svd_feats[pid] = norm_dict(dict(zip(range(n_comp), X_target_svd[i,:])), 'length')
        #np.save('human_eval/corpus_info/svd_feats.npy', svd_feats)
        scores = calc_simcoef_distr(svd_feats, ['cited', 'duplicate', 'random'], 
                                                  id_dict, 'linear')
        auc = calc_auc(scores['cited'], scores['random'])[2]

        plot_score_distr('human_eval', 'linear', ['random', 'cited', 'duplicate'], 
                        {'cited': scores['cited'], 'random': scores['random'], 'duplicate': scores['duplicate']},
                                 auc, ['cited'], histdir='lsa_claims_%i' %n_comp, bins=50)
    '''
