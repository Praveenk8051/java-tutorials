#----------------------------------------------------------------
# Generated CMake target import file for configuration "release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "arch" for configuration "release"
set_property(TARGET arch APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(arch PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "dl;/usr/lib64/libm.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libarch.so"
  IMPORTED_SONAME_RELEASE "libarch.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS arch )
list(APPEND _IMPORT_CHECK_FILES_FOR_arch "${_IMPORT_PREFIX}/lib/libarch.so" )

# Import target "tf" for configuration "release"
set_property(TARGET tf APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(tf PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/python3/lib/libpython3.6m.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libtf.so"
  IMPORTED_SONAME_RELEASE "libtf.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS tf )
list(APPEND _IMPORT_CHECK_FILES_FOR_tf "${_IMPORT_PREFIX}/lib/libtf.so" )

# Import target "gf" for configuration "release"
set_property(TARGET gf APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(gf PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;tf"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libgf.so"
  IMPORTED_SONAME_RELEASE "libgf.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS gf )
list(APPEND _IMPORT_CHECK_FILES_FOR_gf "${_IMPORT_PREFIX}/lib/libgf.so" )

# Import target "js" for configuration "release"
set_property(TARGET js APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(js PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libjs.so"
  IMPORTED_SONAME_RELEASE "libjs.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS js )
list(APPEND _IMPORT_CHECK_FILES_FOR_js "${_IMPORT_PREFIX}/lib/libjs.so" )

# Import target "trace" for configuration "release"
set_property(TARGET trace APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(trace PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;js;tf;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libtrace.so"
  IMPORTED_SONAME_RELEASE "libtrace.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS trace )
list(APPEND _IMPORT_CHECK_FILES_FOR_trace "${_IMPORT_PREFIX}/lib/libtrace.so" )

# Import target "work" for configuration "release"
set_property(TARGET work APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(work PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;trace;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libwork.so"
  IMPORTED_SONAME_RELEASE "libwork.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS work )
list(APPEND _IMPORT_CHECK_FILES_FOR_work "${_IMPORT_PREFIX}/lib/libwork.so" )

# Import target "plug" for configuration "release"
set_property(TARGET plug APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(plug PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;tf;js;trace;work;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libplug.so"
  IMPORTED_SONAME_RELEASE "libplug.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS plug )
list(APPEND _IMPORT_CHECK_FILES_FOR_plug "${_IMPORT_PREFIX}/lib/libplug.so" )

# Import target "vt" for configuration "release"
set_property(TARGET vt APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(vt PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;tf;gf;trace;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libvt.so"
  IMPORTED_SONAME_RELEASE "libvt.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS vt )
list(APPEND _IMPORT_CHECK_FILES_FOR_vt "${_IMPORT_PREFIX}/lib/libvt.so" )

# Import target "ar" for configuration "release"
set_property(TARGET ar APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(ar PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;tf;plug;vt;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libar.so"
  IMPORTED_SONAME_RELEASE "libar.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS ar )
list(APPEND _IMPORT_CHECK_FILES_FOR_ar "${_IMPORT_PREFIX}/lib/libar.so" )

# Import target "kind" for configuration "release"
set_property(TARGET kind APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(kind PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;plug"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libkind.so"
  IMPORTED_SONAME_RELEASE "libkind.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS kind )
list(APPEND _IMPORT_CHECK_FILES_FOR_kind "${_IMPORT_PREFIX}/lib/libkind.so" )

# Import target "sdf" for configuration "release"
set_property(TARGET sdf APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(sdf PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;tf;gf;trace;vt;work;ar;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libsdf.so"
  IMPORTED_SONAME_RELEASE "libsdf.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS sdf )
list(APPEND _IMPORT_CHECK_FILES_FOR_sdf "${_IMPORT_PREFIX}/lib/libsdf.so" )

# Import target "ndr" for configuration "release"
set_property(TARGET ndr APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(ndr PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;plug;vt;work;ar;sdf;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libndr.so"
  IMPORTED_SONAME_RELEASE "libndr.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS ndr )
list(APPEND _IMPORT_CHECK_FILES_FOR_ndr "${_IMPORT_PREFIX}/lib/libndr.so" )

# Import target "sdr" for configuration "release"
set_property(TARGET sdr APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(sdr PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;vt;ar;ndr;sdf;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libsdr.so"
  IMPORTED_SONAME_RELEASE "libsdr.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS sdr )
list(APPEND _IMPORT_CHECK_FILES_FOR_sdr "${_IMPORT_PREFIX}/lib/libsdr.so" )

# Import target "pcp" for configuration "release"
set_property(TARGET pcp APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(pcp PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;trace;vt;sdf;work;ar;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libpcp.so"
  IMPORTED_SONAME_RELEASE "libpcp.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS pcp )
list(APPEND _IMPORT_CHECK_FILES_FOR_pcp "${_IMPORT_PREFIX}/lib/libpcp.so" )

# Import target "usd" for configuration "release"
set_property(TARGET usd APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usd PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;kind;pcp;sdf;ar;plug;tf;trace;vt;work;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusd.so"
  IMPORTED_SONAME_RELEASE "libusd.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usd )
list(APPEND _IMPORT_CHECK_FILES_FOR_usd "${_IMPORT_PREFIX}/lib/libusd.so" )

# Import target "usdGeom" for configuration "release"
set_property(TARGET usdGeom APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdGeom PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "js;tf;plug;vt;sdf;trace;usd;work;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdGeom.so"
  IMPORTED_SONAME_RELEASE "libusdGeom.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdGeom )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdGeom "${_IMPORT_PREFIX}/lib/libusdGeom.so" )

# Import target "usdVol" for configuration "release"
set_property(TARGET usdVol APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdVol PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;usd;usdGeom"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdVol.so"
  IMPORTED_SONAME_RELEASE "libusdVol.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdVol )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdVol "${_IMPORT_PREFIX}/lib/libusdVol.so" )

# Import target "usdLux" for configuration "release"
set_property(TARGET usdLux APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdLux PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;vt;sdf;usd;usdGeom"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdLux.so"
  IMPORTED_SONAME_RELEASE "libusdLux.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdLux )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdLux "${_IMPORT_PREFIX}/lib/libusdLux.so" )

# Import target "usdShade" for configuration "release"
set_property(TARGET usdShade APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdShade PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;vt;sdf;ndr;sdr;usd;usdGeom"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdShade.so"
  IMPORTED_SONAME_RELEASE "libusdShade.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdShade )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdShade "${_IMPORT_PREFIX}/lib/libusdShade.so" )

# Import target "usdRender" for configuration "release"
set_property(TARGET usdRender APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdRender PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "gf;tf;usd;usdGeom"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdRender.so"
  IMPORTED_SONAME_RELEASE "libusdRender.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdRender )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdRender "${_IMPORT_PREFIX}/lib/libusdRender.so" )

# Import target "usdHydra" for configuration "release"
set_property(TARGET usdHydra APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdHydra PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;usd;usdShade"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdHydra.so"
  IMPORTED_SONAME_RELEASE "libusdHydra.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdHydra )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdHydra "${_IMPORT_PREFIX}/lib/libusdHydra.so" )

# Import target "usdRi" for configuration "release"
set_property(TARGET usdRi APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdRi PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;vt;sdf;usd;usdShade;usdGeom;usdLux;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdRi.so"
  IMPORTED_SONAME_RELEASE "libusdRi.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdRi )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdRi "${_IMPORT_PREFIX}/lib/libusdRi.so" )

# Import target "usdSkel" for configuration "release"
set_property(TARGET usdSkel APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdSkel PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;gf;tf;trace;vt;work;sdf;usd;usdGeom;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdSkel.so"
  IMPORTED_SONAME_RELEASE "libusdSkel.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdSkel )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdSkel "${_IMPORT_PREFIX}/lib/libusdSkel.so" )

# Import target "usdUI" for configuration "release"
set_property(TARGET usdUI APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdUI PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;vt;sdf;usd"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdUI.so"
  IMPORTED_SONAME_RELEASE "libusdUI.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdUI )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdUI "${_IMPORT_PREFIX}/lib/libusdUI.so" )

# Import target "usdUtils" for configuration "release"
set_property(TARGET usdUtils APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdUtils PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;tf;gf;sdf;usd;usdGeom;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdUtils.so"
  IMPORTED_SONAME_RELEASE "libusdUtils.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdUtils )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdUtils "${_IMPORT_PREFIX}/lib/libusdUtils.so" )

# Import target "garch" for configuration "release"
set_property(TARGET garch APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(garch PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;tf;/usr/lib64/libSM.so;/usr/lib64/libICE.so;/usr/lib64/libX11.so;/usr/lib64/libXext.so;/usr/lib64/libGL.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libgarch.so"
  IMPORTED_SONAME_RELEASE "libgarch.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS garch )
list(APPEND _IMPORT_CHECK_FILES_FOR_garch "${_IMPORT_PREFIX}/lib/libgarch.so" )

# Import target "hf" for configuration "release"
set_property(TARGET hf APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hf PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "plug;tf;trace"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libhf.so"
  IMPORTED_SONAME_RELEASE "libhf.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS hf )
list(APPEND _IMPORT_CHECK_FILES_FOR_hf "${_IMPORT_PREFIX}/lib/libhf.so" )

# Import target "hio" for configuration "release"
set_property(TARGET hio APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hio PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;hf;tf;trace;vt"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libhio.so"
  IMPORTED_SONAME_RELEASE "libhio.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS hio )
list(APPEND _IMPORT_CHECK_FILES_FOR_hio "${_IMPORT_PREFIX}/lib/libhio.so" )

# Import target "cameraUtil" for configuration "release"
set_property(TARGET cameraUtil APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(cameraUtil PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;gf"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libcameraUtil.so"
  IMPORTED_SONAME_RELEASE "libcameraUtil.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS cameraUtil )
list(APPEND _IMPORT_CHECK_FILES_FOR_cameraUtil "${_IMPORT_PREFIX}/lib/libcameraUtil.so" )

# Import target "pxOsd" for configuration "release"
set_property(TARGET pxOsd APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(pxOsd PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "tf;gf;vt;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/opensubdiv/lib/libosdCPU.a;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/opensubdiv/lib/libosdGPU.a;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libpxOsd.so"
  IMPORTED_SONAME_RELEASE "libpxOsd.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS pxOsd )
list(APPEND _IMPORT_CHECK_FILES_FOR_pxOsd "${_IMPORT_PREFIX}/lib/libpxOsd.so" )

# Import target "glf" for configuration "release"
set_property(TARGET glf APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(glf PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "ar;arch;garch;gf;hf;js;plug;tf;trace;sdf;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so;/usr/lib64/libGL.so;/usr/lib64/libGLU.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/glew/lib/libGLEW.so;/usr/lib64/libSM.so;/usr/lib64/libICE.so;/usr/lib64/libX11.so;/usr/lib64/libXext.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libglf.so"
  IMPORTED_SONAME_RELEASE "libglf.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS glf )
list(APPEND _IMPORT_CHECK_FILES_FOR_glf "${_IMPORT_PREFIX}/lib/libglf.so" )

# Import target "hgi" for configuration "release"
set_property(TARGET hgi APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hgi PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "gf;tf"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libhgi.so"
  IMPORTED_SONAME_RELEASE "libhgi.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS hgi )
list(APPEND _IMPORT_CHECK_FILES_FOR_hgi "${_IMPORT_PREFIX}/lib/libhgi.so" )

# Import target "hgiGL" for configuration "release"
set_property(TARGET hgiGL APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hgiGL PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "arch;hgi;tf;trace;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/glew/lib/libGLEW.so;/usr/lib64/libGL.so;/usr/lib64/libGLU.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libhgiGL.so"
  IMPORTED_SONAME_RELEASE "libhgiGL.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS hgiGL )
list(APPEND _IMPORT_CHECK_FILES_FOR_hgiGL "${_IMPORT_PREFIX}/lib/libhgiGL.so" )

# Import target "hd" for configuration "release"
set_property(TARGET hd APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hd PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "plug;tf;trace;vt;work;sdf;cameraUtil;hf;pxOsd;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libhd.so"
  IMPORTED_SONAME_RELEASE "libhd.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS hd )
list(APPEND _IMPORT_CHECK_FILES_FOR_hd "${_IMPORT_PREFIX}/lib/libhd.so" )

# Import target "hdSt" for configuration "release"
set_property(TARGET hdSt APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hdSt PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "hio;garch;glf;hd;hgiGL;sdr;tf;trace;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/glew/lib/libGLEW.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/opensubdiv/lib/libosdCPU.a;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/opensubdiv/lib/libosdGPU.a"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libhdSt.so"
  IMPORTED_SONAME_RELEASE "libhdSt.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS hdSt )
list(APPEND _IMPORT_CHECK_FILES_FOR_hdSt "${_IMPORT_PREFIX}/lib/libhdSt.so" )

# Import target "hdx" for configuration "release"
set_property(TARGET hdx APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(hdx PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "plug;tf;vt;gf;work;garch;glf;pxOsd;hd;hdSt;hgi;cameraUtil;sdf;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/glew/lib/libGLEW.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libhdx.so"
  IMPORTED_SONAME_RELEASE "libhdx.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS hdx )
list(APPEND _IMPORT_CHECK_FILES_FOR_hdx "${_IMPORT_PREFIX}/lib/libhdx.so" )

# Import target "usdImaging" for configuration "release"
set_property(TARGET usdImaging APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdImaging PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "gf;tf;plug;trace;vt;work;hd;pxOsd;sdf;usd;usdGeom;usdSkel;usdLux;usdShade;usdVol;ar;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdImaging.so"
  IMPORTED_SONAME_RELEASE "libusdImaging.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdImaging )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdImaging "${_IMPORT_PREFIX}/lib/libusdImaging.so" )

# Import target "usdImagingGL" for configuration "release"
set_property(TARGET usdImagingGL APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdImagingGL PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "gf;tf;plug;trace;vt;work;hio;garch;glf;hd;hdx;pxOsd;sdf;sdr;usd;usdGeom;usdHydra;usdShade;usdImaging;ar;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/python3/lib/libpython3.6m.so;/usr/lib64/libGL.so;/usr/lib64/libGLU.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/glew/lib/libGLEW.so;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/tbb/lib/libtbb.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdImagingGL.so"
  IMPORTED_SONAME_RELEASE "libusdImagingGL.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdImagingGL )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdImagingGL "${_IMPORT_PREFIX}/lib/libusdImagingGL.so" )

# Import target "usdSkelImaging" for configuration "release"
set_property(TARGET usdSkelImaging APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdSkelImaging PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "hio;hd;usdImaging;usdSkel"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdSkelImaging.so"
  IMPORTED_SONAME_RELEASE "libusdSkelImaging.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdSkelImaging )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdSkelImaging "${_IMPORT_PREFIX}/lib/libusdSkelImaging.so" )

# Import target "usdVolImaging" for configuration "release"
set_property(TARGET usdVolImaging APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdVolImaging PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "usdImaging"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdVolImaging.so"
  IMPORTED_SONAME_RELEASE "libusdVolImaging.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdVolImaging )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdVolImaging "${_IMPORT_PREFIX}/lib/libusdVolImaging.so" )

# Import target "usdAppUtils" for configuration "release"
set_property(TARGET usdAppUtils APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(usdAppUtils PROPERTIES
  IMPORTED_LINK_INTERFACE_LIBRARIES_RELEASE "garch;gf;glf;sdf;tf;usd;usdGeom;usdImagingGL;/buildAgent/work/a418c88687a09902/usd-build/_dependencies/boost/lib/libboost_python36.so"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libusdAppUtils.so"
  IMPORTED_SONAME_RELEASE "libusdAppUtils.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS usdAppUtils )
list(APPEND _IMPORT_CHECK_FILES_FOR_usdAppUtils "${_IMPORT_PREFIX}/lib/libusdAppUtils.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
