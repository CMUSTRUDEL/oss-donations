import os
import csv

num_models = 2
anova = {}

reader = csv.reader(open('tex_model_all.csv', 'r'), delimiter="&")
big_table = []
trim_big_table = []
for row in reader:
    big_table.append(row)
    trim_big_table.append([e.strip() for e in row])

first_col = []
for r in trim_big_table:
    if len(r):
        first_col.append(r[0])
    else:
        first_col.append('')

coeffs_start = first_col.index(u'(Intercept)')
coeffs_end = first_col.index(u'\\hline', coeffs_start)
coeffs = {}
for i, coeff in enumerate(first_col[coeffs_start:coeffs_end]):
    coeffs[coeff] = coeffs_start + i

#print sorted(coeffs.items(), key=lambda t:int(t[1]))

def latex(s):
    if len(s.split())>1:
        return "%s}" % s.replace(' ', '^{')
    else:
        return s

for i in range(1,num_models+1):
    print(i, '******')
    anova.setdefault(i, {})
    reader = csv.reader(open('anova_model_%d.csv' % i, 'r'), delimiter="&")
    for row in reader:
        trim_row = [e.strip() for e in row]
        print(trim_row)
        if len(trim_row) > 1:
            coeff = trim_row[0] #trim_row[1]
            cs = trim_row[-1][:-3] #trim_row[4]
            if coeff in coeffs:
                anova[i][coeff] = latex(cs)
            elif ('%sTRUE' % coeff) in coeffs:
                anova[i]['%sTRUE' % coeff] = latex(cs)
            elif ('%s1' % coeff) in coeffs:
                anova[i]['%s1' % coeff] = latex(cs)
            elif ('%s' % coeff) in coeffs:
                anova[i]['%s' % coeff] = latex(cs)
            else:
                print('\n', coeff)
                if len(coeff.split(':'))==2:
                    cf = '%sTRUE:%s' % (coeff.split(':')[0], coeff.split(':')[1])
                    #print cf, coeff.split(':')[0], coeffs.has_key(cf) #coeffs.has_key('%sTRUE:%s1' % (coeff.split(':')[0].replace('\\','\\\\'), coeff.split(':')[1])):
                    anova[i][cf] = latex(cs)
                    print(cf, latex(cs))



output = []
for i, row in enumerate(big_table):
    if len(trim_big_table[i]):
        if (trim_big_table[i][0].startswith('\\begin{tabular}')):
            pass
    if i >= coeffs_start and i < coeffs_end:
        new_row = [big_table[i][0]]
        for m in range(num_models):
            old_column = trim_big_table[i][1+m]
            coeff = trim_big_table[i][0]
            if m==range(num_models)[-1]:
                new_row.append(' %s ' % old_column.replace(' \\\\',' ') if len(old_column.replace(' \\\\',' ').strip()) else '')
                new_row.append(' %s \\\\' % anova[m+1].get(coeff, u'') if len(anova[m+1].get(coeff, u'')) else ' \\\\')
            else:
                new_row.append(' %s ' % old_column if len(old_column) else ' ')
                new_row.append(' %s ' % anova[m+1].get(coeff, u'') if len(anova[m+1].get(coeff, u'')) else ' ')

        output.append([e.replace('has\\_contribTRUE','has contrib').replace(
                                 'num\\_issues + 1','issues').replace(
                                 'log(issues + 1)','num issues (log)').replace(
                                 'has\\_urlTRUE','has website').replace(
                                 'log\\_num\\_headers','num headers (log)').replace(
                                 'has\\_contactTRUE','has contact info').replace(
                                 #'readmeSize','readme\_size').replace(
                                 'has\\_badgesTRUE','has badges').replace(
                                 'has\\_labelsTRUE','has labels').replace(
                                 'log\\_reverse\\_dependency\\_count','dependents (log)').replace(
                                 'log\\_num\\_download','downloads (log)').replace(
                                 'is\\_orgTRUE','is org').replace(
                                 'is\\_activeTRUE','is active').replace(
                                 'log\\_size\\_GH', 'size (log)').replace(
								 'log\\_num\\_star\\_GH', 'stars (log)').replace(
								 'log\\_num\\_commit\\_total', 'commits (log)').replace(
                                 'age30','project age') for e in new_row])
    else:
        output.append([e.replace('multicolumn{1}{c}','multicolumn{2}{c}').replace(
                                  '\\usepackage{dcolumn}',' ').replace(
                                   'num_team','num\_team').replace(
                                   'D{)}{)}{13)3}', 'D{)}{)}{15)3}@{} D{.}{.}{5.4} | ').replace(
                                   #'D{)}{)}{17)3}@{}','D{)}{)}{15)3}@{} D{.}{.}{5.4} | ').replace(
                                   'D{)}{)}{11)3}', 'D{)}{)}{15)3}@{} D{.}{.}{5.4} | ').replace(
                                   'D{)}{)}{10)3}', 'D{)}{)}{15)3}@{} D{.}{.}{5.4} | ').replace(
                                  #'\\begin{center}',r'\centering \footnotesize').replace(
                                  '\\begin{center}',r'\centering \small').replace(
                                   '\\end{center}',r' ').replace(
                                 '\\begin{table}','\\begin{table}[t]')
                                 for e in row])

print
writer = csv.writer(open('table_model_glm_anova.tex', 'w'), delimiter="&")
for row in output:
    print(row)
    if row == ['\\begin{tabular}{l D{)}{)}{15)3}@{} D{.}{.}{5.4} |  }']:
        #writer.writerow([u'\\begin{tabular}{p{2cm} D{)}{)}{15)3}@{} D{.}{.}{5.4} |  D{)}{)}{15)3}@{} D{.}{.}{5.4} }'])
        writer.writerow(['\\begin{tabular}{p{3cm} D{)}{)}{13)3}@{} D{.}{.}{6.2}  D{)}{)}{13)3}@{} D{.}{.}{6.2} }'])
        continue
    if row == [' ', ' \\multicolumn{2}{c}{m1} \\\\']:
        writer.writerow([' ', ' \\multicolumn{2}{c}{\\textbf{Early-stage abandoners}} \\\\ '])
        writer.writerow([' ', u' \\multicolumn{1}{c}{Coeffs (Errors)} ', u' \\multicolumn{1}{c}{Deviance} \\\\'])
    #if row == [u'                                               ', u' \\multicolumn{2}{c}{Small Teams} ', u' \\multicolumn{2}{c}{Medium Teams} ', u' \\multicolumn{2}{c}{Large Teams} \\\\']:
    #    writer.writerow([u'                                               ', u' \\multicolumn{2}{c|}{Small Teams} ', u' \\multicolumn{2}{c|}{Medium Teams} ', u' \\multicolumn{2}{c}{Large Teams} \\\\'])
    #    writer.writerow([u'                                               ', u' \\multicolumn{1}{c}{Coeffs (Errors)} ', u' \\multicolumn{1}{c|}{Sum Sq.} ', u' \\multicolumn{1}{c}{Coeffs (Errors)} ', u' \\multicolumn{1}{c|}{Sum Sq.} ', u' \\multicolumn{1}{c}{Coeffs (Errors)} ', u' \\multicolumn{1}{c}{Sum Sq.} \\\\',])
        continue
    writer.writerow(row)
