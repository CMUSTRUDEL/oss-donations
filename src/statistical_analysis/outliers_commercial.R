hist(d$log_num_star_GH) # ok

hist(d$log_num_commit) # mostly ok
table(d$num_commit == 0)
# aggregate(d$num_commit, by=list(d$has_any_funding), FUN=summary)
# table(d[d$has_any_funding == FALSE,]$num_commit == 0)
# table(d[d$has_any_funding == TRUE,]$num_commit == 0)
table(d$num_commit > exp(8))

hist(d$age)
table(d$age > 3200)

hist(d$log_num_committer) # not ok
hist(d$num_committer)
table(d$num_committer > exp(5))
hist(d[d$num_committer <= exp(5),]$log_num_committer)

hist(d$num_external) # not ok
hist(d$log_num_external) # not ok
table(d$num_external > exp(6.5))
hist(d[d$num_external <= exp(6.5),]$log_num_external)

hist(d$size_GH) # not ok
hist(d$log_size_GH) # ok

hist(d$num_download)
hist(d$log_num_download) # ok

hist(d$reverse_dependency_count) # not ok
hist(d$log_reverse_dependency_count) # exp(9)
table(d$reverse_dependency_count > exp(8))
hist(d[d$reverse_dependency_count <= exp(8),]$log_reverse_dependency_count)

hist(d$log_num_commit_total) # ok

hist(d$log_num_committer_total)
table(d$num_committer_total == 0) # strange
table(d$num_committer_total > exp(6))

hist(d$log_num_external_total) # ok

