When depending on a core, versacore will do a so called "core lookup".
It works similarly to path lookup in an OS. An environment variable, $VERSACORE_CORE_PATH,
contains the paths to be looked up in order of priority, delimited by ':'.

The core "repos" can be structured hierarchially. In this case, this will have to be specified in the .depend_on() call,
e.g. .depend_on("silicom/communication/i2c_controller")

If a core from a specific repo is desired, the lookup mechanism can also be overriden in the call to .depend_on().
