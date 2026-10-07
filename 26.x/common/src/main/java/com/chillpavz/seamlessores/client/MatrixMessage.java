package com.chillpavz.seamlessores.client;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.platform.Services;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.HoverEvent;
import net.minecraft.network.chat.MutableComponent;

import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * A short note in chat about the companion mod, Seamless Ores: Matrix. Client only; each loader calls
 * {@link #onClientTick} from its own end-of-tick event.
 *
 * <p>It shows a few seconds after the player enters a world, and only:
 * <ul>
 *   <li>the first time this note is seen on this installation, i.e. on installing the mod or
 *       updating to the version that introduced it (a one-line marker file in the config folder
 *       remembers it), or
 *   <li>in a world that has only just been created (its game time is still under a minute).
 * </ul>
 * Never when Matrix is already installed. Changing {@link #NOTE} makes it show once more to everyone.
 *
 * <p>It goes through {@code LocalPlayer.sendSystemMessage}, which is the same on every 26.x version;
 * the chat component itself moved when 26.2 split {@code Gui} into {@code Gui} and {@code Hud}.
 */
public final class MatrixMessage {

    private static final String MATRIX_MOD_ID = "seamlessoresmatrix";
    private static final URI CURSEFORGE =
            URI.create("https://www.curseforge.com/minecraft/mc-mods/seamless-ores-matrix");

    /** What the marker file holds once the note has been seen. */
    private static final String NOTE = "matrix-1";
    private static final String MARKER = Constants.MOD_ID + "-note.txt";

    /** Three seconds in the world, so the note is not buried under the join messages. */
    private static final int DELAY_TICKS = 60;
    /** A world younger than this (in game ticks) when the note is due counts as new. */
    private static final long NEW_WORLD_TICKS = 1200L;

    /** Decided once per world joined; reset when the player leaves. */
    private static boolean decided;
    private static int ticksInWorld;

    private MatrixMessage() {
    }

    public static void onClientTick(Minecraft minecraft) {
        try {
            final LocalPlayer player = minecraft.player;
            if (player == null || minecraft.level == null) {
                decided = false;
                ticksInWorld = 0;
                return;
            }
            if (decided || ++ticksInWorld < DELAY_TICKS) {
                return;
            }
            decided = true;
            if (Services.PLATFORM.isModLoaded(MATRIX_MOD_ID)) {
                return;
            }
            final Path marker = minecraft.gameDirectory.toPath().resolve("config").resolve(MARKER);
            final boolean firstTime = !NOTE.equals(readMarker(marker));
            final boolean newWorld = minecraft.level.getGameTime() < NEW_WORLD_TICKS;
            if (!firstTime && !newWorld) {
                return;
            }
            player.sendSystemMessage(message());
            Constants.LOG.info("Showed the Seamless Ores: Matrix note in chat ({})",
                    firstTime ? "first time on this installation" : "new world");
            if (firstTime) {
                writeMarker(marker);
            }
        } catch (RuntimeException | LinkageError e) {
            // A chat note is never worth a crash.
            decided = true;
            Constants.LOG.warn("Could not show the Seamless Ores: Matrix note in chat", e);
        }
    }

    private static String readMarker(Path marker) {
        try {
            return Files.isRegularFile(marker) ? Files.readString(marker, StandardCharsets.UTF_8).trim() : null;
        } catch (IOException e) {
            return null;
        }
    }

    private static void writeMarker(Path marker) {
        try {
            Files.createDirectories(marker.getParent());
            Files.writeString(marker, NOTE + "\n", StandardCharsets.UTF_8);
        } catch (IOException e) {
            // Unwritable config folder: the note may show again next time, which is harmless.
            Constants.LOG.warn("Could not save {}, so the Matrix note may show again", marker, e);
        }
    }

    static MutableComponent message() {
        final MutableComponent link = Component.literal("[Open on CurseForge]").withStyle(style -> style
                .withColor(ChatFormatting.GREEN)
                .withUnderlined(true)
                .withClickEvent(new ClickEvent.OpenUrl(CURSEFORGE))
                .withHoverEvent(new HoverEvent.ShowText(Component.literal(CURSEFORGE.toString())
                        .withStyle(ChatFormatting.GRAY))));

        return Component.literal("[Seamless Ores] ").withStyle(ChatFormatting.GOLD)
                .append(Component.literal("New companion mod: ").withStyle(ChatFormatting.YELLOW))
                .append(Component.literal("Seamless Ores: Matrix").withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD))
                .append(Component.literal("\nOres that match the stones other mods add, from Create's layers"
                        + " to Mythic Upgrades schists.").withStyle(ChatFormatting.WHITE))
                .append(Component.literal("\nLive on CurseForge now").withStyle(ChatFormatting.GREEN))
                .append(Component.literal(", not on Modrinth yet. ").withStyle(ChatFormatting.LIGHT_PURPLE))
                .append(link);
    }
}
