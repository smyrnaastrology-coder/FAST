import 'package:flutter/material.dart';

import '../config/theme.dart';

/// İlk açılışta gösterilen 3 adımlı "ilk 5 dakika" akışı.
///
/// Amaç: kullanıcıyı harita/analiz kalabalığına boğmadan, tek bir örnek
/// soruyla horary deneyimini yaşatmak. Metinler tr/en/es olarak burada
/// tutulur; yeni dil eklenirse [_Copy.forLanguage] genişletilir.
class FirstRunOnboarding extends StatefulWidget {
  /// `null` soru: kullanıcı kendi sorusunu yazacak. Dolu soru: horary ekranı
  /// hazır soruyla açılır.
  final ValueChanged<String?> onStart;

  /// "Şimdi değil" — ana ekrana döner, bir daha gösterilmez.
  final VoidCallback onSkip;

  const FirstRunOnboarding({
    super.key,
    required this.onStart,
    required this.onSkip,
  });

  @override
  State<FirstRunOnboarding> createState() => _FirstRunOnboardingState();
}

class _FirstRunOnboardingState extends State<FirstRunOnboarding> {
  final _page = PageController();
  int _index = 0;
  String? _question;

  @override
  void dispose() {
    _page.dispose();
    super.dispose();
  }

  void _next(_Copy copy) {
    if (_index < 2) {
      _page.nextPage(
        duration: const Duration(milliseconds: 260),
        curve: Curves.easeOutCubic,
      );
      return;
    }
    _finish();
  }

  void _finish() {
    Navigator.of(context).pop();
    widget.onStart(_question);
  }

  void _skip() {
    Navigator.of(context).pop();
    widget.onSkip();
  }

  @override
  Widget build(BuildContext context) {
    final lang = Localizations.localeOf(context).languageCode;
    final copy = _Copy.forLanguage(lang);
    return Dialog.fullscreen(
      backgroundColor: FastTheme.bg,
      child: SafeArea(
        child: Column(
          children: [
            Align(
              alignment: Alignment.centerRight,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(8, 8, 12, 0),
                child: TextButton(
                  onPressed: _skip,
                  child: Text(
                    copy.skip,
                    style: TextStyle(color: FastTheme.textDim, fontSize: 13),
                  ),
                ),
              ),
            ),
            Expanded(
              child: PageView(
                controller: _page,
                onPageChanged: (i) => setState(() => _index = i),
                children: [
                  _IntroPage(copy: copy),
                  _HowPage(copy: copy),
                  _QuestionPage(
                    copy: copy,
                    selected: _question,
                    onSelect: (q) => setState(() => _question = q),
                  ),
                ],
              ),
            ),
            _Dots(index: _index),
            const SizedBox(height: 16),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => _next(copy),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: FastTheme.accentGold,
                    foregroundColor: FastTheme.bg,
                    padding: const EdgeInsets.symmetric(vertical: 15),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  child: Text(
                    _index < 2
                        ? copy.next
                        : (_question == null ? copy.writeOwn : copy.start),
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _IntroPage extends StatelessWidget {
  final _Copy copy;
  const _IntroPage({required this.copy});

  @override
  Widget build(BuildContext context) {
    return _PageScroll(
      children: [
        _Badge(
          icon: Icons.auto_awesome,
          colors: [FastTheme.accentGold, FastTheme.accentGoldLight],
        ),
        const SizedBox(height: 26),
        Text(
          copy.introTitle,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: FastTheme.accentGold,
            fontSize: 27,
            fontWeight: FontWeight.w700,
            height: 1.2,
          ),
        ),
        const SizedBox(height: 14),
        Text(
          copy.introBody,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: FastTheme.textMuted,
            fontSize: 15,
            height: 1.6,
          ),
        ),
      ],
    );
  }
}

class _HowPage extends StatelessWidget {
  final _Copy copy;
  const _HowPage({required this.copy});

  @override
  Widget build(BuildContext context) {
    return _PageScroll(
      children: [
        _Badge(
          icon: Icons.explore_outlined,
          colors: [FastTheme.secondary, FastTheme.accent],
        ),
        const SizedBox(height: 24),
        Text(
          copy.howTitle,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: FastTheme.textLight,
            fontSize: 23,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 22),
        for (var i = 0; i < copy.steps.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 14),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    color: FastTheme.accentGold.withValues(alpha: 0.16),
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: FastTheme.accentGold.withValues(alpha: 0.45),
                    ),
                  ),
                  child: Center(
                    child: Text(
                      '${i + 1}',
                      style: TextStyle(
                        color: FastTheme.accentGold,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      copy.steps[i],
                      style: TextStyle(
                        color: FastTheme.textLight,
                        fontSize: 14.5,
                        height: 1.5,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

class _QuestionPage extends StatelessWidget {
  final _Copy copy;
  final String? selected;
  final ValueChanged<String> onSelect;
  const _QuestionPage({
    required this.copy,
    required this.selected,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    return _PageScroll(
      children: [
        _Badge(
          icon: Icons.chat_bubble_outline,
          colors: [FastTheme.rose, FastTheme.secondary],
        ),
        const SizedBox(height: 22),
        Text(
          copy.pickTitle,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: FastTheme.textLight,
            fontSize: 23,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          copy.pickBody,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: FastTheme.textMuted,
            fontSize: 13.5,
            height: 1.5,
          ),
        ),
        const SizedBox(height: 20),
        for (final q in copy.questions)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: _QuestionTile(
              text: q,
              selected: selected == q,
              onTap: () => onSelect(q),
            ),
          ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.card_giftcard, size: 15, color: FastTheme.accentGold),
            const SizedBox(width: 6),
            Text(
              copy.freeHint,
              style: TextStyle(color: FastTheme.textDim, fontSize: 12),
            ),
          ],
        ),
      ],
    );
  }
}

class _QuestionTile extends StatelessWidget {
  final String text;
  final bool selected;
  final VoidCallback onTap;
  const _QuestionTile({
    required this.text,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Ink(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
          decoration: BoxDecoration(
            color: selected
                ? FastTheme.accentGold.withValues(alpha: 0.14)
                : FastTheme.cardBg,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: selected
                  ? FastTheme.accentGold
                  : FastTheme.border,
              width: selected ? 1.4 : 1,
            ),
          ),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  text,
                  style: TextStyle(
                    color: selected ? FastTheme.accentGold : FastTheme.textLight,
                    fontSize: 14,
                    fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
                  ),
                ),
              ),
              if (selected)
                Icon(Icons.check_circle, color: FastTheme.accentGold, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  final IconData icon;
  final List<Color> colors;
  const _Badge({required this.icon, required this.colors});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Container(
        width: 84,
        height: 84,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: LinearGradient(colors: colors),
          boxShadow: [
            BoxShadow(
              color: colors.first.withValues(alpha: 0.28),
              blurRadius: 26,
            ),
          ],
        ),
        child: Icon(icon, color: FastTheme.bg, size: 38),
      ),
    );
  }
}

class _PageScroll extends StatelessWidget {
  final List<Widget> children;
  const _PageScroll({required this.children});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 16, 24, 8),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: children,
          ),
        ),
      ),
    );
  }
}

class _Dots extends StatelessWidget {
  final int index;
  const _Dots({required this.index});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        for (var i = 0; i < 3; i++)
          AnimatedContainer(
            duration: const Duration(milliseconds: 220),
            margin: const EdgeInsets.symmetric(horizontal: 4),
            width: i == index ? 22 : 8,
            height: 8,
            decoration: BoxDecoration(
              color: i == index
                  ? FastTheme.accentGold
                  : FastTheme.accentGold.withValues(alpha: 0.28),
              borderRadius: BorderRadius.circular(8),
            ),
          ),
      ],
    );
  }
}

class _Copy {
  final String skip;
  final String next;
  final String start;
  final String writeOwn;
  final String introTitle;
  final String introBody;
  final String howTitle;
  final List<String> steps;
  final String pickTitle;
  final String pickBody;
  final String freeHint;
  final List<String> questions;

  const _Copy({
    required this.skip,
    required this.next,
    required this.start,
    required this.writeOwn,
    required this.introTitle,
    required this.introBody,
    required this.howTitle,
    required this.steps,
    required this.pickTitle,
    required this.pickBody,
    required this.freeHint,
    required this.questions,
  });

  static _Copy forLanguage(String lang) {
    switch (lang) {
      case 'en':
        return const _Copy(
          skip: 'Not now',
          next: 'Continue',
          start: 'Ask my first question',
          writeOwn: 'I will write my own',
          introTitle: 'Welcome to Holavon',
          introBody:
              'Horary reads the sky at the exact moment you ask. One clear '
              'question in, one direct answer out.',
          howTitle: 'How it works',
          steps: [
            'Type the one question that is really on your mind.',
            'We cast the chart of this exact moment for you.',
            'You get a clear answer, plus the timing.',
          ],
          pickTitle: 'Pick your first question',
          pickBody:
              'Your first 3 questions are free. Start with one of these, or '
              'write your own.',
          freeHint: 'First 3 questions free',
          questions: [
            'Will I get the job?',
            'Does he/she love me?',
            'Where is my lost item?',
          ],
        );
      case 'es':
        return const _Copy(
          skip: 'Ahora no',
          next: 'Continuar',
          start: 'Hacer mi primera pregunta',
          writeOwn: 'Escribiré la mía',
          introTitle: 'Bienvenido a Holavon',
          introBody:
              'La astrología horaria lee el cielo en el momento exacto en que '
              'preguntas. Una pregunta clara, una respuesta directa.',
          howTitle: 'Cómo funciona',
          steps: [
            'Escribe la única pregunta que de verdad te preocupa.',
            'Levantamos la carta de este momento exacto para ti.',
            'Recibes una respuesta clara y el tiempo estimado.',
          ],
          pickTitle: 'Elige tu primera pregunta',
          pickBody:
              'Tus 3 primeras preguntas son gratis. Empieza con una de estas '
              'o escribe la tuya.',
          freeHint: '3 primeras preguntas gratis',
          questions: [
            '¿Conseguiré el trabajo?',
            '¿Me ama?',
            '¿Dónde está mi objeto perdido?',
          ],
        );
      default:
        return const _Copy(
          skip: 'Şimdi değil',
          next: 'Devam',
          start: 'İlk sorumu sor',
          writeOwn: 'Kendi sorumu yazacağım',
          introTitle: "Holavon'a hoş geldin",
          introBody:
              'Horary, soruyu sorduğun tam anda gökyüzünü okur. Tek net soru '
              'girer, tek net cevap çıkar.',
          howTitle: 'Nasıl çalışır?',
          steps: [
            'Aklındaki tek soruyu yaz.',
            'O anın haritasını senin için çıkarırız.',
            'Net cevabı ve zamanlamayı alırsın.',
          ],
          pickTitle: 'İlk sorunu seç',
          pickBody:
              'İlk 3 sorun ücretsiz. Hazır bir soruyla başla ya da kendi '
              'sorunu yaz.',
          freeHint: 'İlk 3 soru ücretsiz',
          questions: [
            'İşe girecek miyim?',
            'Beni seviyor mu?',
            'Kayıp eşyam nerede?',
          ],
        );
    }
  }
}
