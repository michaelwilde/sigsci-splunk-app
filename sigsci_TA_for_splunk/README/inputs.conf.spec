[script://./bin/sigsci.sh]
interval = 5 * * * *
sourcetype = json-sigsci
source = sigsci
index = sigsci
disabled = 0
start_by_shell=false
batch_size = 10000
incremental_merge = 0

[script://./bin/activity.sh]
interval = 5 * * * *
sourcetype = json-sigsci
source = sigsci-activity
index = sigsci
disabled = 0
start_by_shell=false
batch_size = 10000
incremental_merge = 0
