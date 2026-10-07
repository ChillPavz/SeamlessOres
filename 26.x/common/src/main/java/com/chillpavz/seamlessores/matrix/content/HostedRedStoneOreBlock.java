package com.chillpavz.seamlessores.matrix.content;

import net.minecraft.world.level.block.RedStoneOreBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockState;

/** Redstone ore in a modded stone: vanilla's lit behaviour, the stone's sound. See HostedOreBlock. */
public class HostedRedStoneOreBlock extends RedStoneOreBlock {

    private final HostStone host;

    public HostedRedStoneOreBlock(HostStone host, Properties properties) {
        super(properties);
        this.host = host;
    }

    @Override
    protected SoundType getSoundType(BlockState state) {
        return HostedOreBlock.hostSound(host, super.getSoundType(state));
    }
}
