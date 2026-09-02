import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:open_file/open_file.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../models/analysis_request.dart';
import '../providers/analysis_provider.dart';
import '../services/api_service.dart';
import '../services/billing_service.dart';
import '../widgets/score_display.dart';
import '../widgets/language_switcher.dart';
import '../widgets/section_card.dart';

class ResultsScreen extends StatefulWidget {
  final AnalysisRequest request;
  const ResultsScreen({super.key, required this.request});

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  final _api = ApiService();
  String _chartTab = 'situa_a';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AnalysisProvider>().analizYap(widget.request);
    });
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => Navigator.of(context).maybePop()),
        title: Text(widget.request.modLabel(l10n)), actions: const [LanguageSwitcher()]),
      body: Consumer<AnalysisProvider>(
        builder: (context, provider, _) {
          switch (provider.status) {
            case AnalysisStatus.loading:
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const CircularProgressIndicator(),
                    const SizedBox(height: 20),
                    Text(l10n.loadingSky),
                  ],
                ),
              );
            case AnalysisStatus.error:
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 64, color: Colors.red),
                      const SizedBox(height: 16),
                      Text(l10n.errorTitle, style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 8),
                      Text(provider.error ?? l10n.unknownError, textAlign: TextAlign.center),
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: () => provider.analizYap(widget.request),
                        child: Text(l10n.retryButton),
                      ),
                    ],
                  ),
                ),
              );
            case AnalysisStatus.success:
              return _buildResults(context, provider);
            default:
              return const SizedBox.shrink();
          }
        },
      ),
    );
  }

  Widget _buildResults(BuildContext context, AnalysisProvider provider) {
    final l10n = AppLocalizations.of(context);
    final r = provider.detayliResult ?? provider.result!;
    final sessionId = provider.sessionId ?? '';
    final mod = widget.request.mod;

    final isSingle = mod == 'bireysel_natal' || mod == 'potansiyel_yetenek';
    final uyum = r['uyum_orani']?.toString() ?? '';
    final tork = r['tork']?.toString() ?? '';
    final fraktal = r['fraktal']?.toString() ?? '';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Score cards - gizle bireysel/potansiyel modda
          if (!isSingle) ...[
            Row(
              children: [
                if (uyum.isNotEmpty)
                  ScoreCard(label: l10n.scoreCompatibility, value: uyum.length > 40 ? '${uyum.substring(0, 40)}...' : uyum, color: FastTheme.rose),
                if (tork.isNotEmpty) ...[const SizedBox(width: 8), ScoreCard(label: l10n.scoreVitalityTork, value: tork, color: FastTheme.secondary)],
                if (fraktal.isNotEmpty) ...[const SizedBox(width: 8), ScoreCard(label: l10n.scoreFlowFraktal, value: fraktal, color: FastTheme.accent)],
              ],
            ),
            if (uyum.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(uyum, style: const TextStyle(fontSize: 12, color: FastTheme.textLight)),
            ],
            const SizedBox(height: 16),
          ],

          // Chart tabs
          _chartSection(sessionId, mod, r),

          const SizedBox(height: 16),

          // Score display widget (old)
          if (r['total_skor'] != null || r['toplam_puan'] != null || r['score'] != null)
            ScoreDisplay(skor: (r['total_skor'] ?? r['toplam_puan'] ?? r['score'] ?? 0).toDouble()),

          const SizedBox(height: 12),

          // ---- SECTION CARDS ----

          // Karmik Ev
          if (r['karmik_ev'] != null)
            _buildKarmikEv(r['karmik_ev'] as Map),

          // Bagil Iklim
          if (r['bagil_iklim'] != null && (r['bagil_iklim'] as String).isNotEmpty)
            SectionCard(
              title: l10n.analyzerSectionRelativeClimate,
              icon: Icons.cloud,
              child: HtmlRender(r['bagil_iklim'] as String),
            ),

          // Progression
          if (r['progression'] != null)
            _buildProgression(r['progression']),

          // Hava Durumu
          if (r['hava_durumu'] != null)
            _buildWeather(r['hava_durumu']),

          // Zaman Makinesi
          if (r['zaman_makinesi'] != null)
            _buildTimeMachine(r['zaman_makinesi']),

          // Yildiz Muhurleri
          if (r['yildiz_muhurleri'] is List && (r['yildiz_muhurleri'] as List).isNotEmpty)
            _buildYildizMuhurleri(r['yildiz_muhurleri'] as List),

          // Arap Noktalari
          if (r['arap_noktalari'] != null)
            _buildArapNoktalari(r['arap_noktalari'] as Map, r['arap_sinastri']),

          // Asteroitler
          if (r['asteroitler'] is List && (r['asteroitler'] as List).isNotEmpty)
            _buildAsteroitler(r['asteroitler'] as List),

          // Sabianlar
          if (r['sabianlar'] is List && (r['sabianlar'] as List).isNotEmpty)
            _buildSabianlar(r['sabianlar'] as List),

          // Hayat Alanlari (natal)
          if (r['hayat_alanlari'] is List && (r['hayat_alanlari'] as List).isNotEmpty)
            _buildHayatAlanlari(r['hayat_alanlari'] as List),

          // Potansiyel Alanlar
          if (r['potansiyel_alanlar'] is List && (r['potansiyel_alanlar'] as List).isNotEmpty)
            _buildPotansiyelAlanlar(r['potansiyel_alanlar'] as List),

          // Meslek Onerileri
          if (r['meslek_onerileri'] is List && (r['meslek_onerileri'] as List).isNotEmpty)
            _buildMeslekOnerileri(r['meslek_onerileri'] as List),

          // Solar Return
          if (r['solar_return'] != null)
            _buildHtmlSection(l10n.analyzerSectionSolarReturn, r['solar_return']),

          // Lunar Return
          if (r['lunar_return'] != null)
            _buildHtmlSection(l10n.analyzerSectionLunarReturn, r['lunar_return']),

          // Minor Progress
          if (r['minor_progress'] is List && (r['minor_progress'] as List).isNotEmpty)
            _buildMinorProgress(r['minor_progress'] as List),

          // Chart Yorumu
          if (r['chart_yorumu'] != null)
            _buildHtmlSection(l10n.analyzerSectionChartComment, r['chart_yorumu']),

          // Sifa Receteleri
          if (r['sifa_receteleri'] != null)
            _buildSifaReceteleri(r['sifa_receteleri']),

          // Sifa Receteleri Detay
          if (r['sifa_receteleri_detay'] is List && (r['sifa_receteleri_detay'] as List).isNotEmpty)
            _buildSifaReceteleriDetay(r['sifa_receteleri_detay'] as List),

          // Astrocartography
          if (r['astrokartografi'] != null)
            _buildAstrocartography(r['astrokartografi'] as Map, provider, sessionId, r),

          // Simulation / Radar
          if (provider.simData != null)
            _buildSimulation(provider, sessionId),

          // PDF / Payment
          _buildPdfSection(provider, sessionId),
        ],
      ),
    );
  }

  Widget _chartSection(String sessionId, String mod, Map<String, dynamic> r) {
    final l10n = AppLocalizations.of(context);
    final chartTypes = <String, String>{};
    if (sessionId.isNotEmpty) {
      chartTypes['situa_a'] = l10n.analyzerPersonA;
      chartTypes['situa_b'] = l10n.analyzerPersonB;
    }
    if (r['chartlar'] is List) {
      for (final c in r['chartlar'] as List) {
        if (c is String && !chartTypes.containsKey(c)) chartTypes[c] = c;
      }
    }

    if (chartTypes.isEmpty) return const SizedBox.shrink();

    final tabs = chartTypes.entries.toList();
    return Column(
      children: [
        SizedBox(
          height: 36,
          child: ListView(
            scrollDirection: Axis.horizontal,
            children: tabs.map((e) => Padding(
              padding: const EdgeInsets.only(right: 8),
              child: ChoiceChip(
                label: Text(e.value, style: const TextStyle(fontSize: 12)),
                selected: _chartTab == e.key,
                onSelected: (_) => setState(() => _chartTab = e.key),
                selectedColor: FastTheme.primary.withValues(alpha: 0.3),
              ),
            )).toList(),
          ),
        ),
        const SizedBox(height: 8),
        if (_chartTab == 'situa_a' || _chartTab == 'situa_b' || _chartTab == 'frekans' || _chartTab == 'composite')
          ChartImage(url: _api.getGorselUrl(sessionId, _chartTab), label: chartTypes[_chartTab] ?? _chartTab),
        if (tabs.length > 2)
          ...tabs.skip(2).map((e) => Padding(
            padding: const EdgeInsets.only(top: 12),
            child: ChartImage(url: _api.getGorselUrl(sessionId, e.key), label: e.value),
          )),
      ],
    );
  }

  Widget _buildKarmikEv(Map data) {
    final l10n = AppLocalizations.of(context);
    final items = <Widget>[];
    if (data['rapor_a'] is List) {
      for (final item in data['rapor_a'] as List) {
        items.add(HtmlRender(item.toString()));
        items.add(const SizedBox(height: 8));
      }
    }
    if (data['rapor_b'] is List) {
      for (final item in data['rapor_b'] as List) {
        items.add(HtmlRender(item.toString()));
        items.add(const SizedBox(height: 8));
      }
    }
    if (items.isEmpty) return const SizedBox.shrink();
    return SectionCard(title: l10n.analyzerSectionKarmikHouse, icon: Icons.home_work, child: Column(children: items));
  }

  Widget _buildProgression(dynamic data) {
    final l10n = AppLocalizations.of(context);
    if (data is! List) return const SizedBox.shrink();
    return SectionCard(
      title: l10n.progressionTitle,
      icon: Icons.timeline,
      child: Column(
        children: data.map((item) {
          if (item is Map) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (item['kisi'] != null || item['baslik'] != null)
                    Text('${item['kisi'] ?? item['baslik'] ?? ''}', style: const TextStyle(fontWeight: FontWeight.bold)),
                  if ((item['ilerleme_yili'] ?? 0) > 0)
                    Text(l10n.analyzerProgressionYear((item['ilerleme_yili'] as num).toStringAsFixed(1))),
                  if (item['ay_burcu'] != null) Text(l10n.analyzerMoonSun(item['ay_burcu'], item['gunes_burcu'] ?? '')),
                  if (item['genel_yorum'] != null) HtmlRender(item['genel_yorum']),
                  if (item['ay_aci_yorumlari'] is List)
                    ...((item['ay_aci_yorumlari'] as List).map((aci) => Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(aci['baslik'] ?? '', style: const TextStyle(fontWeight: FontWeight.w600)),
                          Text(aci['yorum'] ?? ''),
                          Text('${aci['aci_turu'] ?? ''} · ${aci['etki'] ?? ''} · ${aci['donem'] ?? ''}',
                            style: const TextStyle(fontSize: 11, color: FastTheme.textLight)),
                        ],
                      ),
                    ))),
                  if ((item['toplam_aci'] ?? 0) > 0)
                    Text(l10n.analyzerTotalAspects(item['toplam_aci']),
                      style: const TextStyle(fontSize: 11, color: FastTheme.textLight, fontStyle: FontStyle.italic)),
                ],
              ),
            );
          }
          return HtmlRender(item.toString());
        }).toList(),
      ),
    );
  }

  Widget _buildWeather(dynamic data) {
    final l10n = AppLocalizations.of(context);
    if (data is! List) return const SizedBox.shrink();
    return SectionCard(
      title: l10n.weatherTitle,
      icon: Icons.wb_sunny,
      child: Column(
        children: data.map((item) {
          if (item is Map) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('🗓️ ${item['tarih'] ?? ''} (${item['gun_ad'] ?? ''})',
                    style: const TextStyle(fontWeight: FontWeight.bold)),
                  if (item['ay_burc'] != null)
                    Text(l10n.analyzerMoonTransitLine(item['ay_derece'] ?? '', item['ay_ev'] ?? '', item['ay_burc']),
                      style: const TextStyle(fontSize: 11, color: FastTheme.accent)),
                  if (item['ortam'] != null)
                    Text(item['ortam'].toString(),
                      style: const TextStyle(fontSize: 12, color: FastTheme.textLight, fontStyle: FontStyle.italic)),
                  if (item['yorum'] != null) HtmlRender(item['yorum']),
                  if (item['mesajlar'] is List)
                    ...((item['mesajlar'] as List).map((m) => HtmlRender(m.toString()))),
                ],
              ),
            );
          }
          return HtmlRender(item.toString());
        }).toList(),
      ),
    );
  }

  Widget _buildTimeMachine(dynamic data) {
    final l10n = AppLocalizations.of(context);
    if (data is! List) return const SizedBox.shrink();
    return SectionCard(
      title: l10n.timeMachineTitle,
      icon: Icons.access_time,
      child: Column(
        children: data.map((item) {
          if (item is Map) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (item['yil'] != null) Text(l10n.analyzerYearLine(item['yil']), style: const TextStyle(fontWeight: FontWeight.bold)),
                  if (item['yorum'] != null) HtmlRender(item['yorum']),
                ],
              ),
            );
          }
          return HtmlRender(item.toString());
        }).toList(),
      ),
    );
  }

  Widget _buildYildizMuhurleri(List data) {
    final l10n = AppLocalizations.of(context);
    return SectionCard(
      title: l10n.analyzerSectionSeals,
      icon: Icons.stars,
      child: Column(
        children: data.map((item) {
          if (item is Map) {
            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: FastTheme.bg,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: FastTheme.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item['baslik']?.toString() ?? '', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: FastTheme.accent)),
                  if (item['icerik'] != null)
                    Padding(padding: const EdgeInsets.only(top: 4), child: Text(item['icerik'].toString(), style: const TextStyle(fontSize: 12))),
                ],
              ),
            );
          }
          return Padding(padding: const EdgeInsets.only(bottom: 4), child: Text(item.toString(), style: const TextStyle(fontSize: 13)));
        }).toList(),
      ),
    );
  }

  Widget _buildAsteroitler(List data) {
    final l10n = AppLocalizations.of(context);
    return SectionCard(
      title: l10n.analyzerSectionAsteroids,
      icon: Icons.star,
      child: Column(
        children: data.take(12).map((item) {
          if (item is Map) {
            final etki = item['etki']?.toString() ?? '';
            return Container(
              margin: const EdgeInsets.only(bottom: 4),
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: FastTheme.bg,
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: FastTheme.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text.rich(TextSpan(children: [
                    TextSpan(text: '${item['asteroit'] ?? ''} ', style: const TextStyle(fontWeight: FontWeight.bold)),
                    TextSpan(text: '($etki) — ${item['kaynak'] ?? ''} → ${item['hedef'] ?? ''}: '),
                    TextSpan(text: '${item['gezegen'] ?? ''}', style: const TextStyle(fontWeight: FontWeight.bold)),
                    TextSpan(text: ' (${item['fark'] ?? ''}°)'),
                  ]), style: const TextStyle(fontSize: 12)),
                  if (item['yorum'] != null)
                    Padding(padding: const EdgeInsets.only(top: 2), child: Text(item['yorum'].toString(), style: const TextStyle(fontSize: 11, color: FastTheme.textLight))),
                ],
              ),
            );
          }
          return Padding(padding: const EdgeInsets.only(bottom: 4), child: Text(item.toString(), style: const TextStyle(fontSize: 13)));
        }).toList(),
      ),
    );
  }

  Widget _buildPotansiyelAlanlar(List data) {
    final l10n = AppLocalizations.of(context);
    return SectionCard(
      title: l10n.analyzerSectionPotential(''),
      icon: Icons.auto_awesome,
      child: Column(
        children: data.map((p) {
          if (p is Map) {
            return Container(
              padding: const EdgeInsets.symmetric(vertical: 8),
              decoration: BoxDecoration(border: Border(bottom: BorderSide(color: FastTheme.border.withValues(alpha: 0.5)))),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('✨ ${p['alan'] ?? ''}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                  if (p['aci'] != null || p['aci_turu'] != null)
                    Text(l10n.analyzerAspectOrb(p['aci'] ?? '', p['orb'] ?? '', p['aci_turu'] ?? ''),
                      style: const TextStyle(fontSize: 11, color: FastTheme.textLight)),
                  if (p['metin'] != null)
                    Padding(padding: const EdgeInsets.only(top: 4), child: Text(p['metin'].toString(), style: const TextStyle(fontSize: 12, height: 1.4))),
                ],
              ),
            );
          }
          return Text(p.toString());
        }).toList(),
      ),
    );
  }

  Widget _buildMeslekOnerileri(List data) {
    final l10n = AppLocalizations.of(context);
    return SectionCard(
      title: l10n.analyzerSectionProfession,
      icon: Icons.work,
      child: Column(
        children: data.map((m) {
          if (m is Map) {
            return Container(
              padding: const EdgeInsets.symmetric(vertical: 8),
              decoration: BoxDecoration(border: Border(bottom: BorderSide(color: FastTheme.border.withValues(alpha: 0.5)))),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${data.indexOf(m) + 1}. ${m['alan'] ?? ''}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                  Text(l10n.analyzerScorePoints(m['yuzde'] ?? '', m['puan'] is num ? (m['puan'] as num).toStringAsFixed(1) : m['puan']),
                    style: const TextStyle(fontSize: 11, color: FastTheme.accent)),
                  if (m['meslekler'] is List)
                    ...((m['meslekler'] as List).map((j) => Padding(
                      padding: const EdgeInsets.only(left: 12, top: 2),
                      child: Text('🧑‍💼 ${j['meslek'] ?? ''} — ${j['aciklama'] ?? ''}',
                        style: const TextStyle(fontSize: 12, color: FastTheme.textLight)),
                    ))),
                ],
              ),
            );
          }
          return Text(m.toString());
        }).toList(),
      ),
    );
  }

  Widget _buildArapNoktalari(Map data, dynamic arapSinastri) {
    final l10n = AppLocalizations.of(context);
    return SectionCard(
      title: l10n.analyzerSectionArabic,
      icon: Icons.gps_fixed,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ...data.entries.map((e) {
            final v = e.value;
            if (v is Map && v.isNotEmpty) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('🔮 ${e.key}', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12, color: FastTheme.accent)),
                    const SizedBox(height: 4),
                    Wrap(
                      spacing: 4, runSpacing: 4,
                      children: v.entries.map((n) {
                        final nv = n.value;
                        if (nv is Map) {
                          final derece = nv['derece'] is num ? (nv['derece'] as num).toStringAsFixed(1) : '${nv['derece'] ?? ''}';
                          return Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: FastTheme.bg,
                              border: Border.all(color: FastTheme.border),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text.rich(TextSpan(children: [
                              TextSpan(text: '${n.key}: ', style: const TextStyle(fontWeight: FontWeight.bold)),
                              TextSpan(text: '$derece° ${nv['burc'] ?? ''} (${nv['ev'] ?? ''}. Ev)'),
                            ]), style: const TextStyle(fontSize: 10)),
                          );
                        }
                        return Text('${n.key}: $nv');
                      }).toList(),
                    ),
                  ],
                ),
              );
            }
            return Padding(padding: const EdgeInsets.only(bottom: 4), child: Text('${e.key}: $v', style: const TextStyle(fontSize: 12)));
          }),
          if (arapSinastri is List && arapSinastri.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text('🔗 ${l10n.analyzerSectionArabicBonds}', style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12, color: FastTheme.accent)),
            const SizedBox(height: 4),
            ...arapSinastri.take(6).map((b) => Container(
              padding: const EdgeInsets.all(6),
              margin: const EdgeInsets.only(bottom: 4),
              decoration: BoxDecoration(
                color: FastTheme.bg,
                border: Border.all(color: FastTheme.border),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    b['tip'] == 'nokta_nokta' ? '🌙 ${b['nokta']}: ${b['fark']}° orb' :
                    b['tip'] == 'capraz_nokta' ? '🔄 ${b['nokta_a']} ↔ ${b['nokta_b']}: ${b['fark']}°' :
                    '⭐ ${b['nokta']} → ${b['gezegen']}: ${b['fark']}° (${b['kaynak']} → ${b['hedef']})',
                    style: const TextStyle(fontSize: 12),
                  ),
                  if (b['yorum'] != null)
                    Padding(padding: const EdgeInsets.only(top: 2), child: Text(b['yorum'].toString(), style: const TextStyle(fontSize: 11, color: FastTheme.textLight))),
                ],
              ),
            )),
          ],
        ],
      ),
    );
  }

  Widget _buildSabianlar(List data) {
    final l10n = AppLocalizations.of(context);
    return SectionCard(
      title: l10n.analyzerSectionSabian,
      icon: Icons.auto_stories,
      child: Column(
        children: data.map((item) {
          if (item is Map) {
            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: FastTheme.bg,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: FastTheme.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (item['gezegen'] != null) Text(item['gezegen'].toString(), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  if (item['derece_str'] != null || item['derece'] != null)
                    Text(item['derece_str']?.toString() ?? '${item['derece']}°', style: const TextStyle(fontSize: 12, color: FastTheme.textLight)),
                  if (item['sembol'] != null) Padding(padding: const EdgeInsets.only(top: 4), child: Text(item['sembol'].toString(), style: const TextStyle(fontSize: 12))),
                ],
              ),
            );
          }
          return HtmlRender(item.toString());
        }).toList(),
      ),
    );
  }

  Widget _buildHayatAlanlari(List data) {
    final l10n = AppLocalizations.of(context);
    return SectionCard(
      title: l10n.analyzerSectionLifeAreas,
      icon: Icons.widgets,
      child: Column(
        children: data.map((item) {
          if (item is Map) {
            final skor = (item['skor'] is num) ? (item['skor'] as num).toDouble() : 0.0;
            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${item['icon'] ?? ''} ${item['etiket'] ?? ''}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                    if (item['skor'] != null) ...[
                      const SizedBox(height: 6),
                      LinearProgressIndicator(value: skor / 100, backgroundColor: FastTheme.border),
                    ],
                    if (item['yorum'] != null) Padding(padding: const EdgeInsets.only(top: 4), child: HtmlRender(item['yorum'])),
                    if (item['oneriler'] is List && (item['oneriler'] as List).isNotEmpty)
                      Wrap(
                        spacing: 6, runSpacing: 6,
                        children: (item['oneriler'] as List).map((o) => Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(color: FastTheme.bg, border: Border.all(color: FastTheme.border), borderRadius: BorderRadius.circular(14)),
                          child: Text('💡 ${o['metin'] ?? ''}', style: const TextStyle(fontSize: 10, color: FastTheme.textLight)),
                        )).toList(),
                      ),
                  ],
                ),
              ),
            );
          }
          return HtmlRender(item.toString());
        }).toList(),
      ),
    );
  }

  Widget _buildMinorProgress(List data) {
    final l10n = AppLocalizations.of(context);
    return SectionCard(
      title: l10n.analyzerSectionMinorProgress,
      icon: Icons.trending_up,
      child: Column(
        children: data.map((p) {
          if (p is Map) {
            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: FastTheme.bg, border: Border.all(color: FastTheme.border), borderRadius: BorderRadius.circular(8)),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(p['tarih'] != null ? '📅 ${p['tarih']} (${p['gun_ad'] ?? ''})' : '📅 ${l10n.analyzerProgressionYear(p['yil'] ?? '')}',
                    style: const TextStyle(color: FastTheme.accent, fontWeight: FontWeight.w600)),
                  if (p['ay_burc'] != null)
                    Text(l10n.analyzerMoonSunHouse(p['ay_ev'] ?? '', p['ay_burc'], p['gunes_burc'] ?? ''),
                      style: const TextStyle(fontSize: 11, color: FastTheme.textLight)),
                  if (p['ortam'] != null)
                    Text(p['ortam'].toString(), style: const TextStyle(fontSize: 11, color: FastTheme.textLight, fontStyle: FontStyle.italic)),
                  if (p['yorumlar'] is List)
                    ...((p['yorumlar'] as List).map((y) => Padding(
                      padding: const EdgeInsets.only(top: 2),
                      child: Text('🔹 $y', style: const TextStyle(fontSize: 12, height: 1.5)),
                    ))),
                ],
              ),
            );
          }
          return Text(p.toString());
        }).toList(),
      ),
    );
  }

  Widget _buildHtmlSection(String title, dynamic data) {
    if (data == null) return const SizedBox.shrink();
    return SectionCard(title: title, icon: Icons.article, child: HtmlRender(data.toString()));
  }

  Widget _buildSifaReceteleri(dynamic data) {
    final l10n = AppLocalizations.of(context);
    if (data == null) return const SizedBox.shrink();
    return SectionCard(
      title: l10n.analyzerSectionHealing,
      icon: Icons.spa,
      child: HtmlRender(data.toString()),
    );
  }

  Widget _buildSifaReceteleriDetay(List data) {
    final l10n = AppLocalizations.of(context);
    return SectionCard(
      title: l10n.analyzerSectionHealingDetail,
      icon: Icons.local_florist,
      child: Column(
        children: data.map((rct) => Container(
          margin: const EdgeInsets.only(bottom: 6),
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(color: FastTheme.bg, border: Border.all(color: FastTheme.border), borderRadius: BorderRadius.circular(8)),
          child: Text(rct.toString(), style: const TextStyle(fontSize: 12, height: 1.6)),
        )).toList(),
      ),
    );
  }

  Widget _buildAstrocartography(Map data, AnalysisProvider provider, String sessionId, Map r) {
    final l10n = AppLocalizations.of(context);
    return FutureBuilder<Map<String, dynamic>>(
      future: BillingService.getStatus(),
      builder: (ctx, snap) {
        final isSub = snap.data?['is_subscribed'] == true;
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()));
        }
        if (!isSub) {
          return SectionCard(
            title: l10n.astrokartografiTitle,
            icon: Icons.public,
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(color: FastTheme.bg, borderRadius: BorderRadius.circular(8), border: Border.all(color: FastTheme.border)),
                  child: Column(
                    children: [
                      const Icon(Icons.lock, size: 36, color: FastTheme.accentGold),
                      const SizedBox(height: 8),
                      Text(l10n.analyzerSectionChartComment, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Text('🔒 ${l10n.analyzerLoadWorldMap} — abonelik gerekli', textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: FastTheme.textLight)),
                      const SizedBox(height: 12),
                      SizedBox(width: double.infinity, child: ElevatedButton.icon(icon: const Icon(Icons.star, size: 16), label: Text('Abone Ol — \$7.99/ay'), style: ElevatedButton.styleFrom(backgroundColor: FastTheme.accentGold), onPressed: () {})),
                      const SizedBox(height: 8),
                      Text('PDF alanlar PDF\'te görür, tarayıcıda görmek için abone olun', textAlign: TextAlign.center, style: const TextStyle(fontSize: 11, color: FastTheme.textLight, fontStyle: FontStyle.italic)),
                    ],
                  ),
                ),
              ],
            ),
          );
        }
        final skor = data['skor'] is Map ? data['skor'] as Map : data;
        return SectionCard(
          title: l10n.astrokartografiTitle,
          icon: Icons.public,
          child: Column(
            children: [
              ..._buildAstroBars(skor, l10n),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () => provider.loadAcgMap(),
                  icon: const Icon(Icons.map, size: 18),
                  label: Text('🌍 ${l10n.analyzerLoadWorldMap}'),
                ),
              ),
              if (provider.acgMapUrl != null) ...[
                const SizedBox(height: 8),
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.network(provider.acgMapUrl!, fit: BoxFit.contain, height: 250),
                ),
              ],
              if (provider.astroData != null) ...[
                const SizedBox(height: 12),
                Text(l10n.alternateUniverseScores, style: const TextStyle(fontWeight: FontWeight.bold)),
                ..._buildAstroBars(provider.astroData!['skor'] is Map ? provider.astroData!['skor'] as Map : provider.astroData!, l10n),
              ],
            ],
          ),
        );
      },
    );
  }

  List<Widget> _buildAstroBars(Map data, AppLocalizations l10n) {
    final categories = ['para', 'huzur', 'tutku', 'kriz'];
    final labels = {
      'para': l10n.astroBarMoney, 'huzur': l10n.astroBarPeace,
      'tutku': l10n.astroBarPassion, 'kriz': l10n.astroBarCrisis,
    };
    final colors = {'para': Colors.green, 'huzur': Colors.blue, 'tutku': Colors.red, 'kriz': Colors.orange};
    final effects = data['etkiler'] is List ? data['etkiler'] as List : <dynamic>[];
    return categories.map((cat) {
      final score = (data[cat] is num) ? (data[cat] as num).toDouble() : 0.0;
      return Padding(
        padding: const EdgeInsets.only(top: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                SizedBox(width: 130, child: Text(labels[cat]!, style: const TextStyle(fontSize: 12))),
                Expanded(child: LinearProgressIndicator(value: score / 100, backgroundColor: Colors.grey[200], color: colors[cat])),
                SizedBox(width: 30, child: Text('${score.toInt()}%', style: const TextStyle(fontSize: 11))),
              ],
            ),
            if (effects.isNotEmpty && cat == categories.first)
              Padding(
                padding: const EdgeInsets.only(left: 130, top: 2),
                child: Text(effects.join(', '), style: const TextStyle(fontSize: 10, color: FastTheme.textLight)),
              ),
          ],
        ),
      );
    }).toList();
  }

  Widget _buildSimulation(AnalysisProvider provider, String sessionId) {
    final l10n = AppLocalizations.of(context);
    final data = provider.simData;
    if (data == null) return const SizedBox.shrink();
    final topSehirler = data['top_sehirler'] as Map? ?? {};
    final kategoriler = ['para', 'huzur', 'tutku', 'kriz'];
    final katEtiket = {
      'para': l10n.astroScoreMoney, 'huzur': l10n.astroScorePeace,
      'tutku': l10n.astroScorePassion, 'kriz': l10n.astroScoreCrisis,
    };
    final katRenk = {'para': Colors.green, 'huzur': Colors.blue, 'tutku': Colors.red, 'kriz': Colors.orange};

    return SectionCard(
      title: l10n.cityCompassTitle,
      icon: Icons.explore,
      child: Column(
        children: kategoriler.map((kat) {
          final sehirler = topSehirler[kat] as List? ?? [];
          if (sehirler.isEmpty) return const SizedBox.shrink();
          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(katEtiket[kat]!, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: katRenk[kat])),
                const SizedBox(height: 4),
                ...sehirler.take(5).map((s) {
                  if (s is Map) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Row(
                        children: [
                          Expanded(child: Text(s['sehir']?.toString() ?? '', style: const TextStyle(fontSize: 12))),
                          if (s['skor'] != null)
                            Text('${s['skor']}', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: katRenk[kat])),
                          const SizedBox(width: 8),
                          if (s['sehir'] != null)
                            InkWell(
                              onTap: () => _onCityTap(provider, s),
                              child: const Icon(Icons.refresh, size: 16, color: FastTheme.primary),
                            ),
                        ],
                      ),
                    );
                  }
                  return Text(s.toString());
                }),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }

  void _onCityTap(AnalysisProvider provider, Map s) {
    final sehirAdi = s['sehir']?.toString() ?? '';
    if (sehirAdi.isEmpty) return;
    _api.geocode(sehirAdi).then((g) {
      provider.loadAlternatif({
        'session_id': provider.sessionId,
        'sehir': sehirAdi,
        'enlem': g['lat'],
        'boylam': g['lon'],
      });
    }).catchError((_) {});
  }

  Widget _buildPdfSection(AnalysisProvider provider, String sessionId) {
    final l10n = AppLocalizations.of(context);
    if (sessionId.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: 8, bottom: 32),
      child: SectionCard(
        title: '📄 ${l10n.analyzerReportTitle}',
        icon: Icons.picture_as_pdf,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 360),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => _downloadPdf(provider, sessionId, widget.request.mod, l10n),
                icon: const Icon(Icons.download, size: 20),
                label: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Text(l10n.downloadPdfButton(widget.request.modLabel(l10n)), style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: FastTheme.accent,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  elevation: 4,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _downloadPdf(AnalysisProvider provider, String sessionId, String mod, AppLocalizations l10n) async {
    final tip = switch (mod) {
      'potansiyel_yetenek' => 'potansiyel',
      'bireysel_natal' => 'natal',
      'ebeveyn_cocuk' => 'ebeveyn',
      _ => 'es_sevgili',
    };
    final url = await _api.getPdfUrl(sessionId, tip);
    try {
      final resp = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 90));
      if (resp.statusCode == 402) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.pdfPaymentRequired)));
        return;
      }
      if (resp.statusCode != 200) {
        throw Exception(l10n.analyzerPdfNotFound('${resp.statusCode}'));
      }
      final dir = await getApplicationDocumentsDirectory();
      final dosya = File('${dir.path}/${sessionId}_$tip.pdf');
      await dosya.writeAsBytes(resp.bodyBytes, flush: true);
      await OpenFile.open(dosya.path);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.analyzerPdfDownloaded(dosya.path))));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l10n.analyzerPdfError('$e'))));
    }
  }
}
