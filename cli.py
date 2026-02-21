"""
Subconscious — CLI Demo (v0.3.0)

Etkileşimli terminal arayüzü.
Bilinçaltı düşünceleri, çağrışım ağı ve duygusal analizleri görselleştirir.
"""
import sys
import os

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.tree import Tree
from rich import box

from subconscious.engine import SubconsciousEngine

console = Console()

# ─── UI Helpers ───────────────────────────────────────────────────────────────

BANNER = """
[bold magenta]
 ███████╗██╗   ██╗██████╗  ██████╗ ██████╗ ███╗   ██╗███████╗ ██████╗██╗ ██████╗ ██╗   ██╗███████╗
 ██╔════╝██║   ██║██╔══██╗██╔════╝██╔═══██╗████╗  ██║██╔════╝██╔════╝██║██╔═══██╗██║   ██║██╔════╝
 ███████╗██║   ██║██████╔╝██║     ██║   ██║██╔██╗ ██║███████╗██║     ██║██║   ██║██║   ██║███████╗
 ╚════██║██║   ██║██╔══██╗██║     ██║   ██║██║╚██╗██║╚════██║██║     ██║██║   ██║██║   ██║╚════██║
 ███████║╚██████╔╝██████╔╝╚██████╗╚██████╔╝██║ ╚████║███████║╚██████╗██║╚██████╔╝╚██████╔╝███████║
 ╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝ ╚═════╝╚═╝ ╚═════╝  ╚═════╝ ╚══════╝
[/bold magenta]
[dim]🧠 AI Bilinçaltı Framework — v0.3.0 (Hibrit Mimari)[/dim]
"""

EMOTION_ICONS = {
    "sevinç": "😊", "güven": "🤝", "korku": "😨", "şaşkınlık": "😲",
    "üzüntü": "😢", "tiksinme": "🤢", "öfke": "😡", "beklenti": "🔮",
    "merak": "🤔", "heyecan": "🤩", "kaygı": "😰", "sakinlik": "😌",
    "nötr": "😐",
}

TREND_ICONS = {
    "improving": "📈 İyiye gidiyor",
    "declining": "📉 Kötüye gidiyor",
    "stable": "➡️ Stabil",
}


def show_subconscious(analysis: dict):
    """Bilinçaltı düşünceleri görselleştir."""
    if not analysis:
        return

    # ─── Çağrışımlar ─────────────────────────────────────────────────
    associations = analysis.get("associations", [])
    if associations:
        table = Table(
            title="🔗 Çağrışımlar",
            box=box.ROUNDED,
            border_style="cyan",
            title_style="bold cyan",
        )
        table.add_column("Bağlantı", style="white", max_width=50)
        table.add_column("Etiketler", style="yellow")
        table.add_column("Duygu", style="magenta", justify="center")

        for a in associations:
            tags = ", ".join(a.get("tags", []))
            weight = a.get("emotional_weight", 0.5)
            bar = "█" * int(weight * 10) + "░" * (10 - int(weight * 10))
            table.add_row(a.get("content", ""), tags, f"{bar} {weight:.1f}")
        console.print(table)

    # ─── Duygusal Analiz ─────────────────────────────────────────────
    emotional_tag = analysis.get("emotional_tag", {})
    if emotional_tag:
        emotion_name = emotional_tag.get("primary_emotion", "nötr")
        icon = EMOTION_ICONS.get(emotion_name, "❓")
        intensity = emotional_tag.get("current_intensity", 0)
        valence = emotional_tag.get("valence", 0)
        priority = emotional_tag.get("memory_priority", 0)

        valence_bar = ""
        if valence < 0:
            neg_blocks = int(abs(valence) * 5)
            valence_bar = f"[red]{'◄' * neg_blocks}[/red]{'─' * (5 - neg_blocks)}│{'─' * 5}"
        else:
            pos_blocks = int(valence * 5)
            valence_bar = f"{'─' * 5}│{'─' * (5 - pos_blocks)}[green]{'►' * pos_blocks}[/green]"

        console.print(Panel(
            f"  {icon} [bold]{emotion_name.upper()}[/bold]  "
            f"yoğunluk: [yellow]{intensity:.2f}[/yellow]  "
            f"valence: {valence_bar}  "
            f"öncelik: [magenta]{priority:.2f}[/magenta]",
            title="🎭 Duygusal Etiket",
            border_style="yellow",
            box=box.ROUNDED,
        ))

    # ─── Aktive Olan Kavramlar ───────────────────────────────────────
    activated = analysis.get("activated_concepts", {})
    if activated:
        tree = Tree("⚡ [bold cyan]Aktive Olan Kavramlar[/bold cyan]")
        sorted_concepts = sorted(activated.items(), key=lambda x: x[1], reverse=True)[:8]
        for concept, activation in sorted_concepts:
            bar_len = int(activation * 20)
            bar = f"[green]{'█' * bar_len}[/green][dim]{'░' * (20 - bar_len)}[/dim]"
            tree.add(f"[white]{concept}[/white]  {bar} {activation:.2f}")
        console.print(tree)

    # ─── Duygusal Ton & Gizli Kalıplar ───────────────────────────────
    tone = analysis.get("emotional_tone", "")
    if tone:
        console.print(f"  [bold yellow]🎵 LLM Duygusal Ton:[/] {tone}")

    patterns = analysis.get("hidden_patterns", "")
    if patterns:
        console.print(f"  [bold blue]🔍 Gizli Kalıplar:[/] {patterns}")

    # ─── Sezgi ────────────────────────────────────────────────────────
    intuition = analysis.get("intuition", "")
    if intuition:
        console.print(Panel(
            f"[italic]{intuition}[/italic]",
            title="💡 Sezgi",
            border_style="magenta",
            box=box.DOUBLE_EDGE,
        ))

    # ─── Çağrışım Ağı İstatistikleri ─────────────────────────────────
    assoc_stats = analysis.get("association_stats", {})
    if assoc_stats and assoc_stats.get("concepts", 0) > 0:
        console.print(
            f"  [dim]🕸  Ağ: {assoc_stats.get('concepts', 0)} kavram, "
            f"{assoc_stats.get('associations', 0)} bağlantı, "
            f"yoğunluk: {assoc_stats.get('density', 0):.3f}[/dim]"
        )

    # Hata
    if "_error" in analysis:
        console.print(f"  [dim red]⚠ Parse hatası: {analysis['_error']}[/dim red]")

    console.print()


def show_memory_stats(engine: SubconsciousEngine):
    """Bellek ve çağrışım ağı istatistiklerini göster."""
    mem_stats = engine.get_memory_stats()
    assoc_stats = engine.get_association_stats()
    emo_trend = engine.get_emotional_trend()

    table = Table(
        title="📊 Sistem Durumu",
        box=box.SIMPLE_HEAVY,
        border_style="green",
    )
    table.add_column("Metrik", style="bold")
    table.add_column("Değer", justify="right")

    # Bellek
    table.add_row("── Bellek ──", "", style="dim")
    table.add_row("  Kısa Süreli (STM)", f"{mem_stats['stm_count']} / {mem_stats['stm_capacity']}")
    table.add_row("  Uzun Süreli (LTM)", str(mem_stats['ltm_count']))

    # Çağrışım ağı
    table.add_row("── Çağrışım Ağı ──", "", style="dim")
    table.add_row("  Kavramlar", str(assoc_stats.get('concepts', 0)))
    table.add_row("  Bağlantılar", str(assoc_stats.get('associations', 0)))
    table.add_row("  Yoğunluk", f"{assoc_stats.get('density', 0):.4f}")
    table.add_row("  Bileşenler", str(assoc_stats.get('components', 0)))

    # Duygusal trend
    table.add_row("── Duygusal Trend ──", "", style="dim")
    trend_text = TREND_ICONS.get(emo_trend.get('trend', 'stable'), '?')
    dominant = emo_trend.get('dominant_emotion', 'nötr')
    icon = EMOTION_ICONS.get(dominant, '❓')
    table.add_row("  Baskın Duygu", f"{icon} {dominant}")
    table.add_row("  Trend", trend_text)
    table.add_row("  Ort. Valence", f"{emo_trend.get('avg_valence', 0):.3f}")

    console.print(table)


def show_dream_report(report):
    """Rüya raporunu görselleştir."""
    console.print(Panel(
        f"  ⏱  Süre: [yellow]{report.duration_seconds:.1f}s[/yellow]\n"
        f"  📖 İncelenen anı: [cyan]{report.memories_reviewed}[/cyan]\n"
        f"  🔗 Yeni bağlantı: [green]{report.new_connections}[/green]\n"
        f"  🗑  Budanan anı: [red]{report.memories_pruned}[/red]",
        title="🌙 Rüya Raporu",
        border_style="blue",
        box=box.DOUBLE_EDGE,
    ))

    if report.patterns_found:
        tree = Tree("🔍 [bold]Keşfedilen Kalıplar[/bold]")
        for p in report.patterns_found:
            tree.add(f"[yellow]{p}[/yellow]")
        console.print(tree)

    if report.dream_thoughts:
        for thought in report.dream_thoughts:
            console.print(Panel(
                f"[italic dim]{thought}[/italic dim]",
                title="💭 Rüya Düşüncesi",
                border_style="dim magenta",
                box=box.ROUNDED,
            ))


def show_connections(engine: SubconsciousEngine):
    """Gizli bağlantıları göster."""
    discoveries = engine.discover_connections(limit=5)
    if not discoveries:
        console.print("[yellow]Henüz yeterli veri yok — daha çok konuşmaya devam edin.[/]")
        return

    table = Table(
        title="🌉 Keşfedilen Gizli Bağlantılar",
        box=box.ROUNDED,
        border_style="magenta",
    )
    table.add_column("Kavram A", style="cyan")
    table.add_column("→ Yol →", style="dim")
    table.add_column("Kavram B", style="cyan")
    table.add_column("Güç", justify="center", style="green")

    for d in discoveries:
        path_str = " → ".join(d["path"][1:-1]) if len(d["path"]) > 2 else "doğrudan"
        bar = "█" * int(d["avg_weight"] * 10)
        table.add_row(d["concept_a"], path_str, d["concept_b"], f"{bar} {d['avg_weight']:.2f}")

    console.print(table)


def show_active_concepts(engine: SubconsciousEngine):
    """En aktif kavramları göster."""
    concepts = engine.get_active_concepts(limit=15)
    if not concepts:
        console.print("[yellow]Henüz kavram yok.[/]")
        return

    tree = Tree("🧩 [bold]Kavram Haritası[/bold]")
    for c in concepts:
        freq_stars = "⭐" * min(5, c["frequency"])
        act_bar = "█" * int(c["activation"] * 10) + "░" * (10 - int(c["activation"] * 10))
        branch = tree.add(
            f"[bold white]{c['concept']}[/bold white]  "
            f"aktiflik: [green]{act_bar}[/green] {c['activation']:.2f}  "
            f"önem: {c['importance']:.2f}  "
            f"tekrar: {freq_stars}"
        )

    console.print(tree)


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main(engine=None):
    console.print(BANNER)
    console.print(Panel(
        "[bold]Komutlar:[/]\n"
        "  [cyan]/sub[/]        — Bilinçaltı modunu aç/kapa\n"
        "  [cyan]/bellek[/]     — Sistem istatistikleri\n"
        "  [cyan]/kavramlar[/]  — Kavram haritası\n"
        "  [cyan]/bağlantılar[/] — Gizli bağlantılar\n"
        "  [cyan]/rüya[/]       — Hemen bir rüya döngüsü çalıştır\n"
        "  [cyan]/rüya durum[/] — Rüya daemon istatistikleri\n"
        "  [cyan]/sıfırla[/]    — Konuşmayı sıfırla\n"
        "  [cyan]/çıkış[/]      — Çıkış",
        border_style="dim",
        box=box.ROUNDED,
    ))

    if engine is None:
        engine = SubconsciousEngine()
    show_sub = False

    while True:
        try:
            console.print()
            user_input = console.input("[bold green]Sen ► [/]").strip()

            if not user_input:
                continue

            # Komutlar
            cmd = user_input.lower()
            if cmd == "/çıkış":
                console.print("[dim]Hoşça kal! 🧠[/dim]")
                break
            elif cmd == "/sub":
                show_sub = not show_sub
                status = "AÇIK ✅" if show_sub else "KAPALI ❌"
                console.print(f"[bold]Bilinçaltı gösterimi: {status}[/]")
                continue
            elif cmd == "/bellek":
                show_memory_stats(engine)
                continue
            elif cmd == "/kavramlar":
                show_active_concepts(engine)
                continue
            elif cmd == "/bağlantılar":
                show_connections(engine)
                continue
            elif cmd == "/sıfırla":
                engine.reset()
                console.print("[yellow]Konuşma sıfırlandı (bellek, ağ ve rüya geçmişi korundu).[/]")
                continue
            elif cmd == "/rüya":
                console.print("[bold magenta]🌙 Rüya başlıyor...[/]")
                with console.status("[bold blue]💤 Rüya görülüyor...[/]", spinner="moon"):
                    report = engine.dream_now(use_llm=True)
                show_dream_report(report)
                continue
            elif cmd == "/rüya durum":
                stats = engine.get_dream_stats()
                table = Table(title="🌙 Rüya Durumu", box=box.ROUNDED, border_style="blue")
                table.add_column("Metrik", style="bold")
                table.add_column("Değer", justify="right")
                table.add_row("Toplam rüya", str(stats['total_dreams']))
                table.add_row("Bulunan bağlantı", str(stats['total_connections_discovered']))
                table.add_row("Budanan anı", str(stats['total_memories_pruned']))
                table.add_row("Bulunan kalıp", str(stats['total_patterns_found']))
                status_icon = "💤" if stats['is_dreaming'] else "⏸"
                table.add_row("Durum", f"{status_icon} {'Rüya görüyor' if stats['is_dreaming'] else 'Uyanık'}")
                console.print(table)
                # Son rüya düşünceleri
                thoughts = engine.get_dream_thoughts(limit=3)
                if thoughts:
                    for t in thoughts:
                        console.print(f"  [dim]💭 {t}[/dim]")
                continue

            # Sohbet
            with console.status("[bold magenta]🧠 Bilinçaltı işliyor...[/]", spinner="dots"):
                result = engine.chat(user_input, show_subconscious=show_sub)

            # Bilinçaltı göster
            if show_sub and "subconscious" in result:
                console.print()
                console.print(Panel(
                    "[bold magenta]── Bilinçaltı Düşünceler ──[/]",
                    box=box.SIMPLE,
                    border_style="magenta",
                ))
                show_subconscious(result["subconscious"])

            # Yanıt
            console.print()
            console.print(Panel(
                Markdown(result["response"]),
                title="[bold blue]🤖 Yanıt[/]",
                border_style="blue",
                box=box.ROUNDED,
                padding=(1, 2),
            ))

        except KeyboardInterrupt:
            console.print("\n[dim]Hoşça kal! 🧠[/dim]")
            break
        except Exception as e:
            console.print(f"[bold red]Hata:[/] {e}")
            console.print("[dim]Ollama çalışıyor mu? → ollama serve[/dim]")


if __name__ == "__main__":
    main()
