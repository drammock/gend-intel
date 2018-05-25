#! /usr/bin/env Rscript

## This script loads scoring data from a speech intelligibility experiment, and
## models the results.

suppressPackageStartupMessages(library(afex))
suppressPackageStartupMessages(library(dplyr))
library(ggplot2)
# install.packages(c("coda", "reshape"))  ## dependencies for coefplot2
# install.packages("coefplot2", repos="http://www.math.mcmaster.ca/bolker/R",
#                  type="source")
library(coefplot2)


## function for factor coding
deviation_coding <- function(x, levs=NULL) {
    if(is.null(levs)) levs <- unique(x)
    x <- factor(x, levels=levs)
    dnames <- list(levels(x), levels(x)[2])
    contrasts(x) <- matrix(c(-0.5, 0.5), nrow=2, dimnames=dnames)
    x
}

## load data
scores <- read.csv(file.path("..", "scores.csv"), row.names=1, as.is=TRUE)
scores <- scores %>% mutate(listener_gend=substr(listener, 3, 3))
scores$listener_gend <- deviation_coding(scores$listener_gend, c("M", "F"))
scores$talker_gend <- deviation_coding(scores$talker_gend, c("M", "F"))

# mark listeners with audiology training (=some exposure to IEEE sentences)
aud_listeners <- scan(file.path("..", "aud-listeners.csv"), character())
scores$aud_student <- scores$listener %in% aud_listeners


## ## ## ## ## ## ## ## ## ## ##
## common graphical elements  ##
## ## ## ## ## ## ## ## ## ## ##
box <- geom_boxplot(outlier.shape=NA, coef=0, lwd=0.5, fill=NA)
boxpts_jitter <- geom_jitter(size=2.5, alpha=0.5, width=0.03)
boxpts_dodge <- geom_jitter(size=2.5, alpha=0.5, position=position_dodge(width=1.5))

## y axis
yaxis_score <- list(ylab("Mean score"), ylim(0, 1))
yaxis_slope <- list(ylab("Slope (score ~ SNR)"),
                    scale_y_continuous(limits=c(0, 0.1), breaks=seq(0, 0.1, 0.02)))

## x axis SNR
db_labeler <- function(x) paste(x, "dB", sep=" ")
xaxis_snr <- list(xlab("SNR"), scale_x_continuous(labels=db_labeler,
                                                  breaks=sort(unique(scores$snr))))
## x axis sentence
scores %>% group_by(sent) %>% summarise(score=mean(score)) %>% 
    arrange(score) %>% pull(sent) -> sent_order
xaxis_sent <- list(xlab("Sentence"), scale_x_discrete(limits=sent_order),
                   theme(axis.text.x=element_text(angle=90, vjust=0.5)))
## x axis gender
xaxis_gend <- list(xlab("Talker gender"))

## legends
legend_gend <- list(labs(colour="Talker\ngender", fill="Talker\ngender"))
legend_aud <- list(labs(colour="AuD\nstudent", fill="AuD\nstudent"))
legend_snr <- list(labs(colour="SNR"), guides(colour=guide_legend(reverse=TRUE)))

## ## ## ## ## ## ## ## ## ## ## ## ##
##  MEAN SCORE BY LISTENER, BY SNR  ##
## ## ## ## ## ## ## ## ## ## ## ## ##
scores %>%
    group_by(snr, listener) %>%
    summarise(score=mean(score)) %>%
    ggplot(mapping=aes(x=snr, y=score)) +
    geom_line(aes(group=listener, colour=listener), alpha=0.5) +
    geom_boxplot(aes(group=snr), outlier.shape=NA, coef=0, lwd=0.5, fill=NA) +
    geom_jitter(aes(group=snr, colour=listener), size=1.5, alpha=0.5, width=0.15) +
    labs(title="Mean score for each listener in each SNR") +
    theme_bw() + yaxis_score + xaxis_snr -> fig1a
ggsave("1a-listener-by-snr.pdf", fig1a, device=cairo_pdf, width=6, height=5)


## ## ## ## ## ## ## ## ## ## ## ##
## MEAN SCORE BY TALKER, BY SNR  ##
## ## ## ## ## ## ## ## ## ## ## ##
scores %>%
    group_by(snr, talker) %>%
    summarise(score=mean(score)) %>%
    ggplot(mapping=aes(x=snr, y=score)) +
    geom_line(aes(group=talker, colour=talker), alpha=0.5) +
    geom_boxplot(aes(group=snr), outlier.shape=NA, coef=0, lwd=0.5, fill=NA) +
    geom_jitter(aes(group=snr, colour=talker), size=1.5, alpha=0.5, width=0.15) +
    labs(title="Mean score for each talker in each SNR") +
    theme_bw() + yaxis_score + xaxis_snr -> fig1b
ggsave("1b-talker-by-snr.pdf", fig1b, device=cairo_pdf, width=6, height=5)


## ## ## ## ## ## ## ## ## ##
## MEAN SCORE BY SENTENCE  ##
## ## ## ## ## ## ## ## ## ##
scores %>%
    group_by(sent, snr) %>%
    summarise(score=mean(score)) %>%
    arrange(sent, snr) %>%
    ggplot(mapping=aes(x=sent, y=score)) +
    geom_point(aes(colour=factor(snr)), size=2) +
    labs(title="Mean scores (across listeners) for each sentence in each SNR") +
    theme_bw() + yaxis_score + xaxis_sent + legend_snr -> fig2
ggsave("2-score-by-sentence.pdf", fig2, device=cairo_pdf, width=25, height=5)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
## SCORE BY SNR AND GENDER (W/ INDIVIDUAL LISTENER DATAPOINTS) ##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
scores %>%
    group_by(snr, talker_gend, listener) %>%
    summarise(score=mean(score)) %>%
    ggplot(aes(x=snr, y=score, group=interaction(snr, talker_gend),
               colour=talker_gend)) + 
    box + boxpts_dodge +
    labs(title="Mean score for each listener in each SNR, split by talker gender") +
    theme_bw() + yaxis_score + xaxis_snr + legend_gend -> fig3a
ggsave("3a-listener-by-snr-by-talkergender.pdf", fig3a,
       device=cairo_pdf, width=7, height=5)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
##  SCORE BY SNR AND GENDER (W/ INDIVIDUAL TALKER DATAPOINTS)  ##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
scores %>%
    group_by(snr, talker_gend, talker) %>%
    summarise(score=mean(score)) %>%
    ggplot(aes(x=snr, y=score, group=interaction(snr, talker_gend),
               colour=talker_gend)) + 
    box + boxpts_dodge +
    labs(title="Mean score for each talker in each SNR, split by talker gender") +
    theme_bw() + yaxis_score + xaxis_snr + legend_gend -> fig3b
ggsave("3b-talker-by-snr-by-talkergender.pdf", fig3b, device=cairo_pdf,
       width=7, height=5)


## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
## AUDIOLOGY STUDENTS VS. OTHER LISTENERS (BY SNR) ##
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
scores %>%
    group_by(snr, aud_student, listener) %>%
    summarise(score=mean(score)) %>%
    ggplot(aes(x=snr, y=score, group=interaction(snr, aud_student),
               colour=aud_student)) +
    box + boxpts_dodge +
    labs(title="Mean score for each listener in each SNR, split by student type") +
    theme_bw() + yaxis_score + xaxis_snr + legend_aud -> fig4
ggsave("4-listener-by-snr-by-audstudent.pdf", fig4, device=cairo_pdf,
       width=7, height=5)


## ## ## ## ## ## ## ## ##
## SNR SLOPE BY TALKER  ##
## ## ## ## ## ## ## ## ##
scores %>%
    group_by(snr, talker) %>%
    ggplot(mapping=aes(x=snr, y=score, group=talker, colour=talker_gend)) +
    geom_smooth(method='lm', lwd=0.5, se=FALSE) +
    labs(title="Score ~ SNR, linear fit for each talker") +
    theme_bw() + yaxis_score + xaxis_snr + legend_gend -> fig5a
ggsave("5a-snr-fits-by-talker.pdf", fig5a, device=cairo_pdf,
       width=5, height=5)


## ## ## ## ## ## ## ## ## ## ##
## SNR SLOPE BY TALKER GENDER ##
## ## ## ## ## ## ## ## ## ## ##
scores %>%
    group_by(talker_gend, talker) %>%
    do(mod=lm(score ~ snr, data=.)) %>%
    mutate(slope=mod$coefficients["snr"],
           inter=mod$coefficients["(Intercept)"]) %>%
    ggplot(aes(x=talker_gend, y=slope, group=talker_gend,
               colour=talker_gend, fill=talker_gend)) +
    box + boxpts_jitter +
    labs(title="Model slope estimates by talker") +
    theme_bw() + yaxis_slope + xaxis_gend + legend_gend -> fig5b
ggsave("5b-snr-slope-by-talker.pdf", fig5b, device=cairo_pdf,
       width=5, height=5)


## ## ## ## ## ## ##
## MODEL FORMULAE ##
## ## ## ## ## ## ##

## null model
nullform <- formula(score ~ (1|talker) + (1|listener) + (1|sent))

## full model, talker_gend fixef & talker ranef
fullform <- formula(score ~ snr * talker_gend + (1|talker) + (1|listener) + (1|sent))

## no talker random effect (ntre)
fullform_ntre <- formula(score ~ snr * talker_gend + (1|listener) + (1|sent))


## ## ## ## ##
##  MODELS  ##
## ## ## ## ##

nullmod <- glmer(nullform, data=scores, family=binomial(link="logit"),
                 control=glmerControl(optimizer="bobyqa"))

fullmod <- mixed(fullform, data=scores, family=binomial(link="logit"),
                 method="LR", control=glmerControl(optimizer="bobyqa"),
                 check_contrasts=FALSE)

fullmod_ntre <- mixed(fullform_ntre, data=scores, family=binomial(link="logit"),
                      method="LR", control=glmerControl(optimizer="bobyqa"),
                      check_contrasts=FALSE)

## ## ## ##
## PLOTS ##
## ## ## ##
cairo_pdf(width=7, height=5, filename="coefplot.pdf")
coefplot2(fullmod, intercept=TRUE)
coefplot2(fullmod_ntre, intercept=TRUE, add=TRUE, col='red', offset=0.1)
dev.off()

save(scores, nullmod, fullmod, fullmod_ntre, file="data-and-models.Rdata")


## ## ## ## ## ##
## SIMULATIONS ##
## ## ## ## ## ##

n_iter <- 1e3
iterations <- seq_len(n_iter)
talkers <- scores %>% select(talker) %>% unique() %>% unlist(use.names=FALSE)
genders <- rep(c("M", "F"), length.out=length(talkers))

results <- data.frame(iteration=iterations, intercept=NaN, snr=NaN,
                      rand_gendM=NaN, interaction=NaN, snr_p=NaN,
                      rand_gend_p=NaN, interaction_p=NaN)
estimate_cols <- c("intercept", "snr", "rand_gendM", "interaction")
signif_cols <- c("snr_p", "rand_gend_p", "interaction_p")

for (i in iterations) {
    rand_gend <- sample(genders, length(genders))
    names(rand_gend) <- talkers
    scores$rand_gend <- deviation_coding(rand_gend[scores$talker], c("M", "F"))
    rand_mod <- glm(score ~ snr * rand_gend, data=scores,
                    family=binomial(link="logit"))
    results[i, estimate_cols] <- rand_mod$coefficients
    results[i, signif_cols] <- summary(rand_mod)$coefficients[2:4, 4]
}

real_mod <- glm(score ~ snr * talker_gend, data=scores,
                family=binomial(link="logit"))
real_eff <- real_mod$coefficients["talker_gendF"]
n_extreme <- sum(abs(results$rand_gendM) >= abs(real_eff))

writeLines(paste(n_extreme, "/", nrow(results), "simulations showed effects",
                 "of gender that were as extreme or more extreme than the",
                 "effect in our data."))




