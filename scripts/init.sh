# shellcheck disable=SC2164
cd "$HOME"

ENV=/home/ec2-user/venv/bin/python
ROOT=/home/ec2-user/Sterling-Square

echo "Environment:" $ENV
echo "Project Root Directory:" $ROOT

echo "Getting Holiday List ..."
$ENV $ROOT/manage.py get_holidays

echo "Syncing Credentials ..."
$ENV $ROOT/manage.py resync_creds

echo "Loading Symbols ..."
$ENV $ROOT/manage.py load_symbols

echo "Getting Company Info ..."
$ENV $ROOT/manage.py get_company_info
