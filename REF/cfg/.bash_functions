func_deep_find() {
  sudo find . -name *$1*
}
func_deep_grep() {
  sudo grep -ri $1
}
func_process_find() {
  ps aux | grep $1
}
func_json_pretty() {
  cat ${1} | python -m json.tool
}
