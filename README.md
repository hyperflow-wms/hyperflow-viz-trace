# Visualization of Hyperflow execution traces

`hflow-viz-trace`: generates Gantt chart visualization from [workflow execution logs](https://github.com/hyperflow-wms/log-parser) 

Usage:
```
hflow-viz-trace: converts parsed HyperFlow logs into Gantt chart of workflow execution
Usage:
  hflow-viz-trace [-d|--show] [-a|--show-active-jobs] -s|--source <parsed logs directory>
Options:
  -s --source <dir>      Directory with parsed logs
  -d --show              Display plot instead of saving to file
  -a --show-active-jobs  Display the number of active jobs subplot 
```
