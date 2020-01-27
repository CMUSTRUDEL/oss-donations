Sys.setenv(RSTUDIO_PANDOC="C:/Program Files/RStudio/bin/pandoc")
rmarkdown::render("donations.Rmd", output_file="donations.html")
