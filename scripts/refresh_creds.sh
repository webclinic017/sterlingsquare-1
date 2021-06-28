# shellcheck disable=SC2164
cd "$HOME"

ENV=/home/ec2-user/venv/bin/python
ROOT=/home/ec2-user/Sterling-Square

echo "Environment ", $ENV
echo "Project Root ", $ROOT

echo "Refreshing Credentials ... "
$ENV $ROOT/manage.py resync_creds
