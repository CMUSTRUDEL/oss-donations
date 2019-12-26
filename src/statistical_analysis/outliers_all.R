hist(d$log_num_star_GH) # not ok
table(d$log_num_star_GH > 9)

hist(d$log_num_commit) # not ok
table(d$num_commit == 0)
aggregate(d$num_commit, by=list(d$has_any_funding), FUN=summary)
table(d[d$has_any_funding == FALSE,]$num_commit == 0)
table(d[d$has_any_funding == TRUE,]$num_commit == 0)
# -> model a binary is_active

hist(d$age)
table(d$age > 4800)

hist(d$log_num_committer) # not ok
hist(d$num_committer)
table(d$num_committer > 20)
hist(d[d$num_committer <= 20,]$log_num_committer)
# table(d$num_committer == 0)
# table(d$num_committer == 1)
# table(d$num_committer > 1)

hist(d$num_external) # not ok
hist(d$log_num_external) # not ok
table(d$num_external > 200)
hist(d[d$num_external <= 200,]$log_num_external)

hist(d$size_GH) # not ok
hist(d$log_size_GH) # exp(12)
table(d$size_GH > 1000000)
hist(d[d$size_GH <= 1000000,]$log_size_GH)

# hist(d$num_download)
# hist(d$log_num_download)

# hist(d$reverse_dependency_count) # not ok
# hist(d$log_reverse_dependency_count) # exp(6-8)
# table(d$reverse_dependency_count > 1000)
# hist(d[d$reverse_dependency_count <= 1000,]$log_reverse_dependency_count)

hist(d$log_num_commit_total)
table(d$num_commit_total > 15000)
table(d$num_commit_total == 0)

hist(d$log_num_committer_total)
table(d$num_committer_total == 0) # strange
table(d$num_committer_total > 100)

hist(d$log_num_external_total)
table(d$num_external_total > 1000)

