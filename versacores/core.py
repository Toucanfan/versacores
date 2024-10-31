from versacores.coreapi import vcapi_v0_1 as vc

# The idea is to run core_create() synchronously to configure the dependency tree
# The other functions can be run asynchronously to speed up compilation.
# The idea is to wrap the methods like this:

# for dep in core.dependencies (do this asynchronously (using AsyncIO.wait_for() ?) so they run in parallel):
#     await dep.get_generate(dep)
# await core.generate(core)

NAME = "testcore"
VERSION = "0.0.1"
API_VERSION = "0.1"
DESCRIPTION = "A test core"
    
def TOP(core):
    x7_target = core.define_target("xilinx7")
    x7_target.set_core_parameters(arg1="abcd", arg2="efgh", kwarg1=True)
    x7_target.set_hdl_parameters(param1=1, param2="value")
    x7_target.set_global_vlog_defines(TECH="XILINX_ULTRASCALE")
    x7_target.set_flow("vivado", opts={})
    x7_target.set_global_vars(TECH="TECH_ULTRASCALE")
    core.set_default_target("xilinx7")

def CREATE(core: vc.CoreCreateView, arg1, arg2, kwarg1=False):
    # The backend should concat. the args and hash them, in order to find out whether this instance of the core is unique.
    # If not (i.e. core has been instantiated with same parameters before), use the already existing instance.
    #core.is_singleton(True) # This will cause the backend to report an error if this core is instantiated with more than 1 set of parameters. Consider enabling it by default.
    core.depend_on(name="abc_core", ver="0.1.1", repo="file:///opt/cores", kwarg1=True, kwarg2="ramstyle") # An idea with standardized parameter names, e.g. vc_rtl_suffix for use in rtl template identifiers?
    core.depend_on(name="def_core", ver="0.1.1", repo="git://github.com/my_vc_repo @ v1.0", kwarg1=True, kwarg2="ramstyle")
    core.depend_on(name="ghi_core", ver="0.1.1", repo="vcrepo://myhost.com/vcrepo", kwarg1=True, kwarg2="ramstyle") # Similar to APT with implicit .tar.gz files containing metadata
    core.depend_on_foreign(name="fuse_core", type="fusesoc")
    core.depend_on_foreign(name="implst_core", type="importlist", path="/path/to/importlist")
    #core.return_params(**kwargs) #Return parameters to the instantiator? Maybe we need a more flexible "negotiation"?
    #core.conf_dict["BUS_WIDTH"] = core.dependencies["abc_core"].return_params["BUS_WIDTH"]  # How to use returned parameters
    #core.set_vlog_defines(MYDEF="123")
    core.conf_dict["TECH"] = core.global_vars.get("TECH", "TECH_AGILEX7") # Use this to pass information to subsequent stages

async def GENERATE(core: vc.CoreGenerateView):
    # .core_generate() of any dependencies should all have been run at this stage, hence we can use the results
    hdl_deps = core.dependencies["abc_core"].hdl_files
    await core.run_cmd(f"make hdl HDLDEPS={hdl_deps}") # This will start an external program, which we will asynchronously await on
    core.add_files("hdl/*.v") # When adding a file, the backend should check that: a) File path has not been added before, b) entity has not been added before (yes, requires parsing)
    core.add_files("hdl/*.sv")
    core.add_files("hdl/top.vhd", type="vhdl", useIn="implementation")
    core.add_files("hdl/top_sim.vhd", type="vhdl", useIn="simulation")
    hdl_deps = core.dependencies["abc_core"].hdl_files
    #core.add_files("outputs/firmware.hex", alias="firmware_binary")  # This would be done by a core delivering a firmware binary to its instantiator
    #binfile = core.dependencies["testcore"].aliased_files["firmware_binary"]  # This would be done by the instantiating core to retreive it
    if core.is_top:
        core.add_files(f"syn/{core.target}/timing.sdc", useIn="implementation")
        core.add_files(f"syn/{core.target}/pnr.xdc", useIn="implementation")
    core.set_top("hdl/top.vhd")

async def CLEAN(core: vc.CoreCleanView):
    core.run_cmd("make clean")

async def GET_SOURCES(core: vc.CoreGetSourcesView):
    await core.download("git://user@host:repo @ <ref>", rename_to="source1")
    await core.download("https://www.myhost.com/src2.tar.gz", md5="abcdef01234123123", autoextract=False)
    await core.download("file:///opt/cores/iic_controller", rename_to="i2c")

async def PREPARE_SOURCES(core: vc.CorePrepareSourcesView):
    await core.extract_source("src2.tar.gz", cmd="tar -xzf {}")
    core.apply_patch("source1.patch", cwd="source1") # Move to generate stage?
    core.preprocess_j2("hdl/*.vhd", TECH=core.conf_dict["TECH"]) # Move to generate stage?
    core.namespacify("hdl/*.vhd", "testcore") # Should parse the RTL and add namespace prefixes to all design elements
