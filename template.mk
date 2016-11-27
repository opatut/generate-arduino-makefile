INCLUDES     = {includes}
OBJDIR       = {build_dir}
SRCDIR       = {source_dir}
LIB_DIRS     = {lib_dirs}
CORE_PATH    = {core_path}
VARIANT_PATH = {variant_path}

CORE_DIRS    = $(CORE_PATH) $(VARIANT_PATH)

# http://blog.jgc.org/2011/07/gnu-make-recursive-wildcard-function.html
rwildcard=$(foreach d,$(filter-out .%,$(wildcard $1*)),$(call rwildcard,$d/,$2) $(filter $(subst *,%,$2),$d))

get_objects=$(1:%=%.o)

PROJECT_SRCS     := $(call rwildcard,$(SRCDIR),*.c *.cpp *.S)
PROJECT_SRC_OBJS := $(call get_objects,$(PROJECT_SRCS))
PROJECT_OBJS     := $(patsubst $(SRCDIR)/%,$(OBJDIR)/%,$(PROJECT_SRC_OBJS))

CORE_SRCS     := $(call rwildcard,$(CORE_DIRS),*.c *.cpp *.S)
CORE_SRC_OBJS := $(call get_objects,$(CORE_SRCS))
CORE_OBJS     := $(foreach dir,$(CORE_DIRS),$(patsubst $(dir)/%,$(OBJDIR)/core/%,$(filter $(dir)/%,$(CORE_SRC_OBJS))))

LIB_SRCS     := $(call rwildcard,$(LIB_DIRS),*.c *.cpp *.S)
LIB_SRC_OBJS := $(call get_objects,$(LIB_SRCS))
LIB_OBJS     := $(foreach lib,$(LIB_DIRS),$(patsubst $(lib)/%,$(OBJDIR)/libs/%,$(filter $(lib)/%,$(LIB_SRC_OBJS))))

OBJS = $(PROJECT_OBJS) $(LIB_OBJS) $(CORE_OBJS)

all: {extract_targets}

{compiler_steps}

# the core library
$(OBJDIR)/core.a: $(OBJS) $(CORE_OBJS)
	{silent}mkdir -p $(dir $@)
	{silent}for obj in $^; do {recipe_a}; done

$(OBJDIR)/{project_name}.elf: $(PROJECT_OBJS) $(LIB_OBJS) $(OBJDIR)/core.a
	{silent}mkdir -p $(dir $@)
	{silent}{recipe_combine}

{extractions}

upload: {results}
	{silent}{reset}
	{silent}{upload}
