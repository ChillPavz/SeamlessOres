package com.chillpavz.seamlessores.mixin;

import org.objectweb.asm.tree.ClassNode;
import org.spongepowered.asm.mixin.extensibility.IMixinConfigPlugin;
import org.spongepowered.asm.mixin.extensibility.IMixinInfo;

import java.util.List;
import java.util.Set;

/**
 * Applies only the dripstone mixin whose target this Minecraft version has.
 *
 * <p>One jar serves 26.1.x ({@code DripstoneUtils}) and 26.2 up ({@code SpeleothemUtils}). Both
 * mixins are {@code @Pseudo}, so the absent one is skipped either way, but the loader still tries to
 * read its target first and logs a warning about the missing class on every launch. Answering here
 * stops that attempt.
 *
 * <p>The class files are looked up as resources, never loaded: loading a Minecraft class this early
 * would bypass the mixins meant for it. If neither file can be found the lookup itself is not working
 * on this loader, and both mixins are left to {@code @Pseudo} rather than both being switched off.
 */
public final class SeamlessOresMixinPlugin implements IMixinConfigPlugin {

    private static final String DRIPSTONE_UTILS = "net.minecraft.world.level.levelgen.feature.DripstoneUtils";
    private static final String SPELEOTHEM_UTILS = "net.minecraft.world.level.levelgen.feature.SpeleothemUtils";

    private boolean hasDripstoneUtils;
    private boolean hasSpeleothemUtils;

    @Override
    public void onLoad(String mixinPackage) {
        hasDripstoneUtils = exists(DRIPSTONE_UTILS);
        hasSpeleothemUtils = exists(SPELEOTHEM_UTILS);
        if (!hasDripstoneUtils && !hasSpeleothemUtils) {
            hasDripstoneUtils = true;
            hasSpeleothemUtils = true;
        }
    }

    private static boolean exists(String className) {
        final ClassLoader loader = SeamlessOresMixinPlugin.class.getClassLoader();
        return loader != null && loader.getResource(className.replace('.', '/') + ".class") != null;
    }

    @Override
    public boolean shouldApplyMixin(String targetClassName, String mixinClassName) {
        if (DRIPSTONE_UTILS.equals(targetClassName)) {
            return hasDripstoneUtils;
        }
        if (SPELEOTHEM_UTILS.equals(targetClassName)) {
            return hasSpeleothemUtils;
        }
        return true;
    }

    @Override
    public String getRefMapperConfig() {
        return null;
    }

    @Override
    public void acceptTargets(Set<String> myTargets, Set<String> otherTargets) {
    }

    @Override
    public List<String> getMixins() {
        return null;
    }

    @Override
    public void preApply(String targetClassName, ClassNode targetClass, String mixinClassName, IMixinInfo mixinInfo) {
    }

    @Override
    public void postApply(String targetClassName, ClassNode targetClass, String mixinClassName, IMixinInfo mixinInfo) {
    }
}
