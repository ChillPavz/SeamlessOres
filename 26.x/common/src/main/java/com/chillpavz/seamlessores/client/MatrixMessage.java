package com.chillpavz.seamlessores.client;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.matrix.MatrixPresence;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * A short note in chat that Seamless Ores: Matrix is now part of Seamless Ores. Client only; each loader
 * calls {@link #onClientTick} from its own end-of-tick event.
 *
 * <p>It shows a few seconds after the player enters a world:
 * <ul>
 *   <li>on every world joined while the old Matrix mod is still installed, asking the player to remove
 *       it (until then it keeps placing its ores under its own ids, and ours stand down);
 *   <li>otherwise once on this installation, the first time after updating to the version that merged
 *       it (a one-line marker file in the config folder remembers it).
 * </ul>
 * Changing {@link #NOTE} makes the one-time note show once more to everyone.
 *
 * <p>It goes through {@code LocalPlayer.sendSystemMessage}, which is the same on every 26.x version;
 * the chat component itself moved when 26.2 split {@code Gui} into {@code Gui} and {@code Hud}.
 */
public final class MatrixMessage {

    /** What the marker file holds once the one-time note has been seen. */
    private static final String NOTE = "matrix-merged-1";
    private static final String MARKER = Constants.MOD_ID + "-note.txt";

    /** Three seconds in the world, so the note is not buried under the join messages. */
    private static final int DELAY_TICKS = 60;

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
            if (MatrixPresence.oldMatrixInstalled()) {
                player.sendSystemMessage(removeMatrix());
                Constants.LOG.info("Showed the note to remove Seamless Ores: Matrix in chat");
                return;
            }
            final Path marker = minecraft.gameDirectory.toPath().resolve("config").resolve(MARKER);
            if (NOTE.equals(readMarker(marker))) {
                return;
            }
            player.sendSystemMessage(merged());
            Constants.LOG.info("Showed the Seamless Ores: Matrix merge note in chat (first time on this installation)");
            writeMarker(marker);
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

    private static MutableComponent header() {
        return Component.literal("[Seamless Ores] ").withStyle(ChatFormatting.GOLD)
                .append(Component.literal("Seamless Ores: Matrix").withStyle(ChatFormatting.AQUA, ChatFormatting.BOLD))
                .append(Component.literal(" is now part of Seamless Ores.").withStyle(ChatFormatting.YELLOW));
    }

    static MutableComponent merged() {
        return header()
                .append(Component.literal("\nOres in the stones other mods add come with it, with nothing"
                        + " else to install.").withStyle(ChatFormatting.WHITE));
    }

    static MutableComponent removeMatrix() {
        return header()
                .append(Component.literal("\nPlease remove Seamless Ores: Matrix from your mods folder.")
                        .withStyle(ChatFormatting.RED))
                .append(Component.literal(" Its ores already in your worlds carry over.")
                        .withStyle(ChatFormatting.WHITE));
    }
}
