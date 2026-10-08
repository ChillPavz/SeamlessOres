package com.chillpavz.seamlessores.content;

import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockState;

/**
 * An ore in a host stone. Sounds like the stone rather than like the ore it stands in for, as vanilla's
 * deepslate ores sound like deepslate.
 *
 * <p>The sound cannot be baked into the block properties: a host may belong to another mod, which may
 * not have registered yet when we do. So it is read from the stone on use, and falls back to the
 * ore's own sound if the stone does not resolve.
 */
public class HostedOreBlock extends DropExperienceBlock {

    private final HostStone host;

    public HostedOreBlock(HostStone host, IntProvider xp, Properties properties) {
        super(xp, properties);
        this.host = host;
    }

    @Override
    protected SoundType getSoundType(BlockState state) {
        return hostSound(host, super.getSoundType(state));
    }

    static SoundType hostSound(HostStone host, SoundType fallback) {
        final Block stone = host.block();
        return stone == null ? fallback : stone.defaultBlockState().getSoundType();
    }
}
