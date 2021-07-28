# .bashrc
source /srv/venv/bin/activate

alias datanommer-consumer-start="sudo systemctl start datanommer.service && echo 'datanommer consumer is running'"
alias datanommer-consumer-logs="sudo journalctl -u datanommer.service"
alias datanommer-consumer-restart="sudo systemctl restart datanommer.service && echo 'datanommer consumer is running'"
alias datanommer-consumer-stop="sudo systemctl stop datanommer.service && echo 'datanommer service stopped'"
