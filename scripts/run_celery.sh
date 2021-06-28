#! /bin/bash
#celery -A sterling_square  worker -B -l info

ENV=/home/ec2-user/venv/bin/celery
ROOT=/home/ec2-user/Sterling-Square

# move to project root
# shellcheck disable=SC2164
cd $ROOT;

# Kill celery
pkill celery;

# remove previous nohup.out
rm -f nohup.out;

# run celery command
nohup $ENV -A sterling_square  worker -B -l info &
date
