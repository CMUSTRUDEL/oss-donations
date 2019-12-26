library(stringr)

# Write to file
print_tex = function(file, tex){
  fileConn=file(file)
  writeLines(tex, fileConn)
  close(fileConn)
}


makeTexReg = function(mList, file, modelNames, caption, digits=5){
  fileConn=file(file)
  for(i in 1:length(modelNames))
  {
    caption=paste(caption, " Model ",modelNames[i],sep="")
  }
  writeLines(texreg(mList, #$mPR$printModels,
                    naive=TRUE, 
                    single.row=TRUE, 
                    # custom.model.names=c("Small Teams","Medium Teams","Large Teams"), 
                    caption=caption,
                    dcolumn=TRUE,
                    digits=digits,
                    scriptsize=TRUE), 
             fileConn)
  close(fileConn)
}


makeTexRegCox = function(mList, file, modelNames, caption, digits=5){
  fileConn=file(file)
  coeffs = list()
  for(i in 1:length(modelNames))
  {
    caption=paste(caption, " Model ",modelNames[i],sep="")
    coeffs = append(coeffs, list(mList[[i]]$coefficients))
  }
  writeLines(texreg(mList, #$mPR$printModels,
                    naive=TRUE, 
                    single.row=TRUE, 
                    override.coef=as.list(coeffs),
                    # custom.model.names=c("Small Teams","Medium Teams","Large Teams"), 
                    caption=caption,
                    dcolumn=TRUE,
                    digits=digits,
                    scriptsize=TRUE), 
             fileConn)
  close(fileConn)
}


makeTexReg1 = function(mList, file, modelNames, caption, digits=5){
  fileConn=file(file)
  for(i in 1:length(modelNames))
  {
    caption=paste(caption, " Model ",modelNames[i],sep="")
  }
  writeLines(texreg(mList[[1]],
                    naive=TRUE, 
                    single.row=TRUE, 
                    custom.model.names=modelNames, 
                    caption=caption,
                    dcolumn=TRUE,
                    digits=digits,
                    scriptsize=TRUE), 
             fileConn)
  close(fileConn)
}

make.fs = function(anova, symbols) {
  sig.symbols = c("", " *", " **", " ***")
  ifelse(anova[["Pr(>F)"]] < 0.001, 
         str_c(formatC(anova[["F"]], 
                       digits = 2,
                       format = "f"), 
               symbols[4]), 
         ifelse(anova[["Pr(>F)"]] < 0.01, 
                str_c(formatC(anova[["F"]], 
                              digits = 2, 
                              format = "f"), 
                      symbols[3]), 
                ifelse(anova[["Pr(>F)"]] < 0.05, 
                       str_c(formatC(anova[["F"]], 
                                     digits = 2, 
                                     format = "f"), 
                             symbols[2]), 
                       ifelse(anova[["Pr(>F)"]] < 0.1, 
                              str_c(formatC(anova[["F"]], 
                                            digits = 2, 
                                            format = "f"), 
                                    symbols[1]), 
                              formatC(anova[["F"]], 
                                      digits = 2, 
                                      format = "f"))
                )
         )
  )
}

print_anova = function(m, file){
  sig.symbols = c("", " *", " **", " ***")
  fileConn=file(file)
  a=anova(m)
  a.out = cbind(a, data.frame(F = make.fs(a, sig.symbols), 
                              stringsAsFactors = FALSE))
  a.out$F = paste(sprintf("%.2f", round(a.out[,1],2)), a.out[,7], sep="")
  text = print(xtable(a.out))
  writeLines(text, fileConn)
  close(fileConn)
}


print_Anova = function(m, file){
  sig.symbols = c("", " *", " **", " ***")
  fileConn=file(file)
  a=Anova(m, type=2)
  a.out = cbind(a, data.frame(F = make.fs(a, sig.symbols), 
                              stringsAsFactors = FALSE))
  a.out$F = paste(sprintf("%.2f", round(a.out[,1],2)), a.out[,5], sep="")
  text = print(xtable(a.out))
  writeLines(text, fileConn)
  close(fileConn)
}


make.fs.glm = function(anova, symbols) {
  sig.symbols = c("", " *", " **", " ***")
  formatC(anova[["Deviance"]], 
          digits = 2, 
          format = "f")
}

make.fs.glm2 = function(anova, symbols) {
  sig.symbols = c("", " *", " **", " ***")
  ifelse(anova[["Pr(>Chisq)"]] < 0.001, 
         str_c(formatC(anova[["LR Chisq"]], 
                       digits = 2,
                       format = "f"), 
               symbols[4]), 
         ifelse(anova[["Pr(>Chisq)"]] < 0.01, 
                str_c(formatC(anova[["LR Chisq"]], 
                              digits = 2, 
                              format = "f"), 
                      symbols[3]), 
                ifelse(anova[["Pr(>Chisq)"]] < 0.05, 
                       str_c(formatC(anova[["LR Chisq"]], 
                                     digits = 2, 
                                     format = "f"), 
                             symbols[2]), 
                       ifelse(anova[["Pr(>Chisq)"]] < 0.1, 
                              str_c(formatC(anova[["LR Chisq"]], 
                                            digits = 2, 
                                            format = "f"), 
                                    symbols[1]), 
                              formatC(anova[["LR Chisq"]], 
                                      digits = 2, 
                                      format = "f"))
                )
         )
  )
}


print_anova_glm = function(m, file){
  sig.symbols = c("", " *", " **", " ***")
  fileConn=file(file)
  a=anova(m)
  a.out = cbind(a, data.frame(Deviance = make.fs.glm(a, sig.symbols), 
                              stringsAsFactors = FALSE))
  a.out$Deviance = paste(sprintf("%.2f", round(a.out[,2],2)), a.out[,5], sep="")
  text = print(xtable(a.out))
  writeLines(text, fileConn)
  close(fileConn)
}

print_Anova_glm = function(m, file){
  sig.symbols = c("", " *", " **", " ***")
  fileConn=file(file)
  a=Anova(m, type=2)
  a.out = cbind(a, data.frame(LR_Chisq = make.fs.glm2(a, sig.symbols), 
                              stringsAsFactors = FALSE))
  a.out$LR_Chisq = paste(sprintf("%.2f", round(a.out[,1],2)), a.out[,4], sep="")
  text = print(xtable(a.out))
  writeLines(text, fileConn)
  close(fileConn)
}
