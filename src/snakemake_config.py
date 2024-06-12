# This is a crazy hack. When using "run" in the Snakemake file, there is a magic "config" object,
# which contains the snakemake config: the merged config from all config files and from the command
# line parameter --config. The best way would be to pass the config object or only the relevant
# parameters to the functions that need the information. But for some cases a global variable
# avoids the need to pass the config object around *everywhere*....
#
# This is means that this module needs to be imported first in the Snakemake file and the config
# needs to be set here. Otherwise it will fail.
#
# Access e.g. via: snakemake_config.config["testmode"]
