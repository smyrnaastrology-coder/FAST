import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_tr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('tr'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'FAST'**
  String get appTitle;

  /// No description provided for @appSlogan.
  ///
  /// In en, this message translates to:
  /// **'Stellar Bond Analysis System'**
  String get appSlogan;

  /// No description provided for @navFeatures.
  ///
  /// In en, this message translates to:
  /// **'Features'**
  String get navFeatures;

  /// No description provided for @navPricing.
  ///
  /// In en, this message translates to:
  /// **'Pricing'**
  String get navPricing;

  /// No description provided for @navFaq.
  ///
  /// In en, this message translates to:
  /// **'FAQ'**
  String get navFaq;

  /// No description provided for @navStartAnalysis.
  ///
  /// In en, this message translates to:
  /// **'Start Analysis'**
  String get navStartAnalysis;

  /// No description provided for @heroBadge.
  ///
  /// In en, this message translates to:
  /// **'PROJECTION OF THE STARS ON EARTH'**
  String get heroBadge;

  /// No description provided for @heroTitle.
  ///
  /// In en, this message translates to:
  /// **'Your Bond\'s Celestial'**
  String get heroTitle;

  /// No description provided for @heroTitleAccent.
  ///
  /// In en, this message translates to:
  /// **'Map Awaits'**
  String get heroTitleAccent;

  /// No description provided for @heroSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Discover the depths of your relationship, your child\'s potential, or your own talents with the Fatih Asartepe Synastry Technique (FAST).'**
  String get heroSubtitle;

  /// No description provided for @heroDisclaimer.
  ///
  /// In en, this message translates to:
  /// **'Disclaimer: This work does not predict future events; it is not divination, fortune-telling, or a definitive judgment. It is an analysis guide that explains the projection of the sky at your birth onto the earth from a perspective of personal awareness and development.'**
  String get heroDisclaimer;

  /// No description provided for @freeAnalysis.
  ///
  /// In en, this message translates to:
  /// **'Free Analysis'**
  String get freeAnalysis;

  /// No description provided for @chooseAnalysisType.
  ///
  /// In en, this message translates to:
  /// **'Choose Analysis Type'**
  String get chooseAnalysisType;

  /// No description provided for @statAnalysis.
  ///
  /// In en, this message translates to:
  /// **'Analyses'**
  String get statAnalysis;

  /// No description provided for @statYearCycle.
  ///
  /// In en, this message translates to:
  /// **'Year Cycle'**
  String get statYearCycle;

  /// No description provided for @statCities.
  ///
  /// In en, this message translates to:
  /// **'Cities'**
  String get statCities;

  /// No description provided for @modeSectionTitle.
  ///
  /// In en, this message translates to:
  /// **'Choose Your Analysis Type'**
  String get modeSectionTitle;

  /// No description provided for @modeSectionDesc.
  ///
  /// In en, this message translates to:
  /// **'Start the analysis that suits you best'**
  String get modeSectionDesc;

  /// No description provided for @modeEsTitle.
  ///
  /// In en, this message translates to:
  /// **'Couple / Partner'**
  String get modeEsTitle;

  /// No description provided for @modeEsDesc.
  ///
  /// In en, this message translates to:
  /// **'Bond analysis between couples with a 6-month sky flow'**
  String get modeEsDesc;

  /// No description provided for @modeEsBadge.
  ///
  /// In en, this message translates to:
  /// **'Couple'**
  String get modeEsBadge;

  /// No description provided for @modeEbTitle.
  ///
  /// In en, this message translates to:
  /// **'Parent / Child'**
  String get modeEbTitle;

  /// No description provided for @modeEbDesc.
  ///
  /// In en, this message translates to:
  /// **'Intergenerational bond, child development and potential detection'**
  String get modeEbDesc;

  /// No description provided for @modeEbBadge.
  ///
  /// In en, this message translates to:
  /// **'Family'**
  String get modeEbBadge;

  /// No description provided for @modeNatalTitle.
  ///
  /// In en, this message translates to:
  /// **'Individual Natal'**
  String get modeNatalTitle;

  /// No description provided for @modeNatalDesc.
  ///
  /// In en, this message translates to:
  /// **'Deep analysis for all areas of life with your personal birth chart'**
  String get modeNatalDesc;

  /// No description provided for @modeNatalBadge.
  ///
  /// In en, this message translates to:
  /// **'Personal'**
  String get modeNatalBadge;

  /// No description provided for @modePyTitle.
  ///
  /// In en, this message translates to:
  /// **'Potential / Talent'**
  String get modePyTitle;

  /// No description provided for @modePyDesc.
  ///
  /// In en, this message translates to:
  /// **'Career guidance and talent discovery with your birth chart'**
  String get modePyDesc;

  /// No description provided for @modePyBadge.
  ///
  /// In en, this message translates to:
  /// **'Individual'**
  String get modePyBadge;

  /// No description provided for @featuresTitle.
  ///
  /// In en, this message translates to:
  /// **'What Do We Offer?'**
  String get featuresTitle;

  /// No description provided for @featuresDesc.
  ///
  /// In en, this message translates to:
  /// **'Explore every dimension of astrological analysis with FAST'**
  String get featuresDesc;

  /// No description provided for @feature1Title.
  ///
  /// In en, this message translates to:
  /// **'Synastry Analysis'**
  String get feature1Title;

  /// No description provided for @feature1Desc.
  ///
  /// In en, this message translates to:
  /// **'Deep analysis of your planetary positions with couple, parent-child, individual natal or potential charts.'**
  String get feature1Desc;

  /// No description provided for @feature2Title.
  ///
  /// In en, this message translates to:
  /// **'Astrocartography'**
  String get feature2Title;

  /// No description provided for @feature2Desc.
  ///
  /// In en, this message translates to:
  /// **'Your star compatibility map across 15,000+ cities; explore the projection of planets on Earth.'**
  String get feature2Desc;

  /// No description provided for @feature3Title.
  ///
  /// In en, this message translates to:
  /// **'Star Seals'**
  String get feature3Title;

  /// No description provided for @feature3Desc.
  ///
  /// In en, this message translates to:
  /// **'Your planetary seals in the 21-year celestial cycle and celestial contract analysis.'**
  String get feature3Desc;

  /// No description provided for @feature4Title.
  ///
  /// In en, this message translates to:
  /// **'Sky Time Flow'**
  String get feature4Title;

  /// No description provided for @feature4Desc.
  ///
  /// In en, this message translates to:
  /// **'Relationship, development and opportunity windows with daily, monthly and yearly sky flows.'**
  String get feature4Desc;

  /// No description provided for @feature5Title.
  ///
  /// In en, this message translates to:
  /// **'Potential & Talent'**
  String get feature5Title;

  /// No description provided for @feature5Desc.
  ///
  /// In en, this message translates to:
  /// **'Natural talent detection in 7 different areas and career guidance recommendations.'**
  String get feature5Desc;

  /// No description provided for @feature6Title.
  ///
  /// In en, this message translates to:
  /// **'Asteroid Interactions'**
  String get feature6Title;

  /// No description provided for @feature6Desc.
  ///
  /// In en, this message translates to:
  /// **'Juno, Ceres, Pallas, Vesta, Eros, Psyche — cross contacts of 8 asteroids.'**
  String get feature6Desc;

  /// No description provided for @feature7Title.
  ///
  /// In en, this message translates to:
  /// **'Arabic Points'**
  String get feature7Title;

  /// No description provided for @feature7Desc.
  ///
  /// In en, this message translates to:
  /// **'Analysis of cosmic points with synastry bonds and house positions.'**
  String get feature7Desc;

  /// No description provided for @feature8Title.
  ///
  /// In en, this message translates to:
  /// **'PDF Report'**
  String get feature8Title;

  /// No description provided for @feature8Desc.
  ///
  /// In en, this message translates to:
  /// **'All analyses in a professional PDF report; unlimited downloads and email delivery.'**
  String get feature8Desc;

  /// No description provided for @howTitle.
  ///
  /// In en, this message translates to:
  /// **'How Does It Work?'**
  String get howTitle;

  /// No description provided for @howDesc.
  ///
  /// In en, this message translates to:
  /// **'Your stellar bond analysis in 3 steps'**
  String get howDesc;

  /// No description provided for @step1Title.
  ///
  /// In en, this message translates to:
  /// **'Choose Analysis Type'**
  String get step1Title;

  /// No description provided for @step1Desc.
  ///
  /// In en, this message translates to:
  /// **'Couple, parent-child, individual natal or potential analysis — choose the one that fits you.'**
  String get step1Desc;

  /// No description provided for @step2Title.
  ///
  /// In en, this message translates to:
  /// **'Enter Your Information'**
  String get step2Title;

  /// No description provided for @step2Desc.
  ///
  /// In en, this message translates to:
  /// **'With your name, birth date and location, your 21-year analysis is ready within seconds.'**
  String get step2Desc;

  /// No description provided for @step3Title.
  ///
  /// In en, this message translates to:
  /// **'Get Your PDF Report'**
  String get step3Title;

  /// No description provided for @step3Desc.
  ///
  /// In en, this message translates to:
  /// **'Download your detailed report as PDF, keep it as you wish or receive it via email.'**
  String get step3Desc;

  /// No description provided for @howStart.
  ///
  /// In en, this message translates to:
  /// **'Start Analysis Now'**
  String get howStart;

  /// No description provided for @pricingTitle.
  ///
  /// In en, this message translates to:
  /// **'Pricing'**
  String get pricingTitle;

  /// No description provided for @pricingDesc.
  ///
  /// In en, this message translates to:
  /// **'Choose the package that suits you best'**
  String get pricingDesc;

  /// No description provided for @pricingMonthly.
  ///
  /// In en, this message translates to:
  /// **'Monthly'**
  String get pricingMonthly;

  /// No description provided for @pricingYearly.
  ///
  /// In en, this message translates to:
  /// **'Yearly'**
  String get pricingYearly;

  /// No description provided for @pricingDiscount.
  ///
  /// In en, this message translates to:
  /// **'20% off'**
  String get pricingDiscount;

  /// No description provided for @planFree.
  ///
  /// In en, this message translates to:
  /// **'Free'**
  String get planFree;

  /// No description provided for @planPerYear.
  ///
  /// In en, this message translates to:
  /// **'/year'**
  String get planPerYear;

  /// No description provided for @planPerMonth.
  ///
  /// In en, this message translates to:
  /// **'/month'**
  String get planPerMonth;

  /// No description provided for @planTrial.
  ///
  /// In en, this message translates to:
  /// **'Try Free'**
  String get planTrial;

  /// No description provided for @planStart.
  ///
  /// In en, this message translates to:
  /// **'Start with {plan}'**
  String planStart(Object plan);

  /// No description provided for @planFreeName.
  ///
  /// In en, this message translates to:
  /// **'Basic'**
  String get planFreeName;

  /// No description provided for @planFreeBadge.
  ///
  /// In en, this message translates to:
  /// **'Free'**
  String get planFreeBadge;

  /// No description provided for @planFreeDesc.
  ///
  /// In en, this message translates to:
  /// **'Experience the analysis'**
  String get planFreeDesc;

  /// No description provided for @planFreeFeat1.
  ///
  /// In en, this message translates to:
  /// **'All analysis results on screen'**
  String get planFreeFeat1;

  /// No description provided for @planFreeFeat2.
  ///
  /// In en, this message translates to:
  /// **'2 chart views'**
  String get planFreeFeat2;

  /// No description provided for @planFreeFeat3.
  ///
  /// In en, this message translates to:
  /// **'Basic compatibility scores'**
  String get planFreeFeat3;

  /// No description provided for @planFreeFeat4.
  ///
  /// In en, this message translates to:
  /// **'Sky flow'**
  String get planFreeFeat4;

  /// No description provided for @planFreeFeat5.
  ///
  /// In en, this message translates to:
  /// **'Limited asteroid data'**
  String get planFreeFeat5;

  /// No description provided for @planFreeDisabled1.
  ///
  /// In en, this message translates to:
  /// **'PDF Report'**
  String get planFreeDisabled1;

  /// No description provided for @planFreeDisabled2.
  ///
  /// In en, this message translates to:
  /// **'Astrocartography'**
  String get planFreeDisabled2;

  /// No description provided for @planFreeDisabled3.
  ///
  /// In en, this message translates to:
  /// **'Star Seals'**
  String get planFreeDisabled3;

  /// No description provided for @planFreeDisabled4.
  ///
  /// In en, this message translates to:
  /// **'Arabic Points'**
  String get planFreeDisabled4;

  /// No description provided for @planFreeDisabled5.
  ///
  /// In en, this message translates to:
  /// **'Email PDF'**
  String get planFreeDisabled5;

  /// No description provided for @planPremiumName.
  ///
  /// In en, this message translates to:
  /// **'Premium'**
  String get planPremiumName;

  /// No description provided for @planPremiumBadge.
  ///
  /// In en, this message translates to:
  /// **'Most Popular'**
  String get planPremiumBadge;

  /// No description provided for @planPremiumDesc.
  ///
  /// In en, this message translates to:
  /// **'Professional analysis package'**
  String get planPremiumDesc;

  /// No description provided for @planPremiumFeat1.
  ///
  /// In en, this message translates to:
  /// **'Everything in Basic'**
  String get planPremiumFeat1;

  /// No description provided for @planPremiumFeat2.
  ///
  /// In en, this message translates to:
  /// **'PDF Report (unlimited downloads)'**
  String get planPremiumFeat2;

  /// No description provided for @planPremiumFeat3.
  ///
  /// In en, this message translates to:
  /// **'Astrocartography world map'**
  String get planPremiumFeat3;

  /// No description provided for @planPremiumFeat4.
  ///
  /// In en, this message translates to:
  /// **'Full Star Seals list'**
  String get planPremiumFeat4;

  /// No description provided for @planPremiumFeat5.
  ///
  /// In en, this message translates to:
  /// **'Arabic Points + synastry'**
  String get planPremiumFeat5;

  /// No description provided for @planPremiumFeat6.
  ///
  /// In en, this message translates to:
  /// **'All charts SVG (7+ graphics)'**
  String get planPremiumFeat6;

  /// No description provided for @planPremiumFeat7.
  ///
  /// In en, this message translates to:
  /// **'PDF delivery via email'**
  String get planPremiumFeat7;

  /// No description provided for @planProName.
  ///
  /// In en, this message translates to:
  /// **'Pro'**
  String get planProName;

  /// No description provided for @planProBadge.
  ///
  /// In en, this message translates to:
  /// **'VIP'**
  String get planProBadge;

  /// No description provided for @planProDesc.
  ///
  /// In en, this message translates to:
  /// **'Includes personal consultation'**
  String get planProDesc;

  /// No description provided for @planProFeat1.
  ///
  /// In en, this message translates to:
  /// **'Everything in Premium'**
  String get planProFeat1;

  /// No description provided for @planProFeat2.
  ///
  /// In en, this message translates to:
  /// **'Personal astrology interpretation'**
  String get planProFeat2;

  /// No description provided for @planProFeat3.
  ///
  /// In en, this message translates to:
  /// **'30 minutes WhatsApp consultation'**
  String get planProFeat3;

  /// No description provided for @planProFeat4.
  ///
  /// In en, this message translates to:
  /// **'1 year update right'**
  String get planProFeat4;

  /// No description provided for @planProFeat5.
  ///
  /// In en, this message translates to:
  /// **'Priority support'**
  String get planProFeat5;

  /// No description provided for @testimonialsTitle.
  ///
  /// In en, this message translates to:
  /// **'User Reviews'**
  String get testimonialsTitle;

  /// No description provided for @testimonialsDesc.
  ///
  /// In en, this message translates to:
  /// **'Real user experiences'**
  String get testimonialsDesc;

  /// No description provided for @t1Name.
  ///
  /// In en, this message translates to:
  /// **'Zeynep K.'**
  String get t1Name;

  /// No description provided for @t1Text.
  ///
  /// In en, this message translates to:
  /// **'It let me see the bond between me and my spouse from a very different perspective. The PDF report was incredibly detailed.'**
  String get t1Text;

  /// No description provided for @t2Name.
  ///
  /// In en, this message translates to:
  /// **'Ahmet T.'**
  String get t2Name;

  /// No description provided for @t2Text.
  ///
  /// In en, this message translates to:
  /// **'Thanks to the astrocartography feature we found the city we needed to move to. We are very happy now.'**
  String get t2Text;

  /// No description provided for @t3Name.
  ///
  /// In en, this message translates to:
  /// **'Selin A.'**
  String get t3Name;

  /// No description provided for @t3Text.
  ///
  /// In en, this message translates to:
  /// **'Through our star map we understood the dynamics of difficult periods in our relationship and strengthened our communication.'**
  String get t3Text;

  /// No description provided for @t4Name.
  ///
  /// In en, this message translates to:
  /// **'Mehmet B.'**
  String get t4Name;

  /// No description provided for @t4Text.
  ///
  /// In en, this message translates to:
  /// **'I used it to discover my son\'s talents. The career guidance recommendations were very accurate.'**
  String get t4Text;

  /// No description provided for @t5Name.
  ///
  /// In en, this message translates to:
  /// **'Ayşe K.'**
  String get t5Name;

  /// No description provided for @t5Text.
  ///
  /// In en, this message translates to:
  /// **'I had a potential analysis done for myself. I discovered talent areas I hadn\'t noticed before. It prompted me to change careers.'**
  String get t5Text;

  /// No description provided for @faqTitle.
  ///
  /// In en, this message translates to:
  /// **'Frequently Asked Questions'**
  String get faqTitle;

  /// No description provided for @faqDesc.
  ///
  /// In en, this message translates to:
  /// **'Your questions answered'**
  String get faqDesc;

  /// No description provided for @faq1Q.
  ///
  /// In en, this message translates to:
  /// **'How does the analysis work?'**
  String get faq1Q;

  /// No description provided for @faq1A.
  ///
  /// In en, this message translates to:
  /// **'Your astrological chart is generated with your birth date, time and location. FAST technique calculates relative charts and analyzes the 21-year celestial cycle.'**
  String get faq1A;

  /// No description provided for @faq2Q.
  ///
  /// In en, this message translates to:
  /// **'Which analysis type should I choose?'**
  String get faq2Q;

  /// No description provided for @faq2A.
  ///
  /// In en, this message translates to:
  /// **'If you are married or in a relationship, use the \"Couple/Partner\" mode; to discover your child\'s talents use the \"Parent/Child\" mode.'**
  String get faq2A;

  /// No description provided for @faq3Q.
  ///
  /// In en, this message translates to:
  /// **'I don\'t know my birth time, what should I do?'**
  String get faq3Q;

  /// No description provided for @faq3A.
  ///
  /// In en, this message translates to:
  /// **'Analysis can be done without the birth time, but the house chart and some detailed calculations require the time. If unavailable, 12:00 is used by default.'**
  String get faq3A;

  /// No description provided for @faq4Q.
  ///
  /// In en, this message translates to:
  /// **'How do I get my PDF report?'**
  String get faq4Q;

  /// No description provided for @faq4A.
  ///
  /// In en, this message translates to:
  /// **'You can download your PDF report unlimited times by purchasing the Premium or Pro package. The report is also delivered by email.'**
  String get faq4A;

  /// No description provided for @faq5Q.
  ///
  /// In en, this message translates to:
  /// **'What are the payment methods?'**
  String get faq5Q;

  /// No description provided for @faq5A.
  ///
  /// In en, this message translates to:
  /// **'Credit card, debit card and bank transfer/EFT options are available. All payments are protected with 256-bit SSL.'**
  String get faq5A;

  /// No description provided for @faq6Q.
  ///
  /// In en, this message translates to:
  /// **'Do you offer a money-back guarantee?'**
  String get faq6Q;

  /// No description provided for @faq6A.
  ///
  /// In en, this message translates to:
  /// **'Yes, we offer an unconditional 14-day money-back guarantee. If you are not satisfied, your payment is refunded.'**
  String get faq6A;

  /// No description provided for @faq7Q.
  ///
  /// In en, this message translates to:
  /// **'What is astrocartography?'**
  String get faq7Q;

  /// No description provided for @faq7A.
  ///
  /// In en, this message translates to:
  /// **'It finds the cities where the planets in your birth chart have the strongest influence on Earth.'**
  String get faq7A;

  /// No description provided for @faq8Q.
  ///
  /// In en, this message translates to:
  /// **'How does potential analysis work?'**
  String get faq8Q;

  /// No description provided for @faq8A.
  ///
  /// In en, this message translates to:
  /// **'Your natural talents in 7 different areas are detected by scanning the planetary aspects in your birth chart.'**
  String get faq8A;

  /// No description provided for @ctaTitle.
  ///
  /// In en, this message translates to:
  /// **'Ready to Discover Your Star Map?'**
  String get ctaTitle;

  /// No description provided for @ctaDesc.
  ///
  /// In en, this message translates to:
  /// **'Relationship, family, individual natal or potential analysis — start now to explore your 21-year celestial cycle.'**
  String get ctaDesc;

  /// No description provided for @ctaCouple.
  ///
  /// In en, this message translates to:
  /// **'Start Couple Analysis'**
  String get ctaCouple;

  /// No description provided for @ctaParentChild.
  ///
  /// In en, this message translates to:
  /// **'Parent-Child'**
  String get ctaParentChild;

  /// No description provided for @ctaNatal.
  ///
  /// In en, this message translates to:
  /// **'Individual Natal'**
  String get ctaNatal;

  /// No description provided for @ctaPotential.
  ///
  /// In en, this message translates to:
  /// **'Potential Analysis'**
  String get ctaPotential;

  /// No description provided for @footerTagline.
  ///
  /// In en, this message translates to:
  /// **'Stellar bond analysis with the Fatih Asartepe Synastry Technique (FAST).'**
  String get footerTagline;

  /// No description provided for @footerQuickLinks.
  ///
  /// In en, this message translates to:
  /// **'Quick Links'**
  String get footerQuickLinks;

  /// No description provided for @footerContact.
  ///
  /// In en, this message translates to:
  /// **'Contact'**
  String get footerContact;

  /// No description provided for @footerRights.
  ///
  /// In en, this message translates to:
  /// **'© 2024 FAST. All rights reserved.'**
  String get footerRights;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @turkish.
  ///
  /// In en, this message translates to:
  /// **'Turkish'**
  String get turkish;

  /// No description provided for @english.
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get english;

  /// No description provided for @homeTitle.
  ///
  /// In en, this message translates to:
  /// **'Fatih Asartepe\nSynastry Technique'**
  String get homeTitle;

  /// No description provided for @homeSubtitle.
  ///
  /// In en, this message translates to:
  /// **'FAST — Stellar Bond Analysis System'**
  String get homeSubtitle;

  /// No description provided for @homeVersion.
  ///
  /// In en, this message translates to:
  /// **'Version 4.0'**
  String get homeVersion;

  /// No description provided for @analyzerSimulationSelect.
  ///
  /// In en, this message translates to:
  /// **'Select Simulation'**
  String get analyzerSimulationSelect;

  /// No description provided for @analyzerModeEsDesc.
  ///
  /// In en, this message translates to:
  /// **'6-month sky flow'**
  String get analyzerModeEsDesc;

  /// No description provided for @analyzerModeEbDesc.
  ///
  /// In en, this message translates to:
  /// **'Intergenerational bond analysis'**
  String get analyzerModeEbDesc;

  /// No description provided for @analyzerModeNatalDesc.
  ///
  /// In en, this message translates to:
  /// **'Personal birth chart'**
  String get analyzerModeNatalDesc;

  /// No description provided for @analyzerModePyDesc.
  ///
  /// In en, this message translates to:
  /// **'Birth chart analysis'**
  String get analyzerModePyDesc;

  /// No description provided for @analyzerLoading.
  ///
  /// In en, this message translates to:
  /// **'Analyzing...'**
  String get analyzerLoading;

  /// No description provided for @analyzerStart.
  ///
  /// In en, this message translates to:
  /// **'Start Analysis'**
  String get analyzerStart;

  /// No description provided for @analyzerPerson1.
  ///
  /// In en, this message translates to:
  /// **'1st Person'**
  String get analyzerPerson1;

  /// No description provided for @analyzerPerson2.
  ///
  /// In en, this message translates to:
  /// **'2nd Person'**
  String get analyzerPerson2;

  /// No description provided for @analyzerName.
  ///
  /// In en, this message translates to:
  /// **'Name'**
  String get analyzerName;

  /// No description provided for @analyzerBirthDate.
  ///
  /// In en, this message translates to:
  /// **'Birth Date'**
  String get analyzerBirthDate;

  /// No description provided for @analyzerMeetingMarriage.
  ///
  /// In en, this message translates to:
  /// **'Meeting / Marriage'**
  String get analyzerMeetingMarriage;

  /// No description provided for @analyzerDate.
  ///
  /// In en, this message translates to:
  /// **'Date'**
  String get analyzerDate;

  /// No description provided for @analyzerTime.
  ///
  /// In en, this message translates to:
  /// **'Time'**
  String get analyzerTime;

  /// No description provided for @analyzerParent.
  ///
  /// In en, this message translates to:
  /// **'Parent'**
  String get analyzerParent;

  /// No description provided for @analyzerRole.
  ///
  /// In en, this message translates to:
  /// **'Role'**
  String get analyzerRole;

  /// No description provided for @analyzerMother.
  ///
  /// In en, this message translates to:
  /// **'Mother'**
  String get analyzerMother;

  /// No description provided for @analyzerFather.
  ///
  /// In en, this message translates to:
  /// **'Father'**
  String get analyzerFather;

  /// No description provided for @analyzerChild.
  ///
  /// In en, this message translates to:
  /// **'Child'**
  String get analyzerChild;

  /// No description provided for @analyzerBirthTime.
  ///
  /// In en, this message translates to:
  /// **'Birth Time'**
  String get analyzerBirthTime;

  /// No description provided for @analyzerPersonalInfo.
  ///
  /// In en, this message translates to:
  /// **'Personal Information'**
  String get analyzerPersonalInfo;

  /// No description provided for @analyzerLocation.
  ///
  /// In en, this message translates to:
  /// **'Location'**
  String get analyzerLocation;

  /// No description provided for @analyzerCountry.
  ///
  /// In en, this message translates to:
  /// **'Country'**
  String get analyzerCountry;

  /// No description provided for @analyzerCity.
  ///
  /// In en, this message translates to:
  /// **'City'**
  String get analyzerCity;

  /// No description provided for @analyzerLatitude.
  ///
  /// In en, this message translates to:
  /// **'Latitude'**
  String get analyzerLatitude;

  /// No description provided for @analyzerLongitude.
  ///
  /// In en, this message translates to:
  /// **'Longitude'**
  String get analyzerLongitude;

  /// No description provided for @analyzerSearchLocation.
  ///
  /// In en, this message translates to:
  /// **'Search Location'**
  String get analyzerSearchLocation;

  /// No description provided for @analyzerOptional.
  ///
  /// In en, this message translates to:
  /// **'optional'**
  String get analyzerOptional;

  /// No description provided for @analyzerBirthDateHint.
  ///
  /// In en, this message translates to:
  /// **'08.10.1986'**
  String get analyzerBirthDateHint;

  /// No description provided for @analyzerDateRequired.
  ///
  /// In en, this message translates to:
  /// **'Enter the birth date'**
  String get analyzerDateRequired;

  /// No description provided for @analyzerDate2Required.
  ///
  /// In en, this message translates to:
  /// **'Enter the 2nd person\'s birth date'**
  String get analyzerDate2Required;

  /// No description provided for @analyzerNameRequired.
  ///
  /// In en, this message translates to:
  /// **'Enter a name'**
  String get analyzerNameRequired;

  /// No description provided for @analyzerCityNotFound.
  ///
  /// In en, this message translates to:
  /// **'City not found, enter manually'**
  String get analyzerCityNotFound;

  /// No description provided for @analyzerSearchHint.
  ///
  /// In en, this message translates to:
  /// **'Type a city and press search'**
  String get analyzerSearchHint;

  /// No description provided for @analyzerSelectCity.
  ///
  /// In en, this message translates to:
  /// **'Select a city'**
  String get analyzerSelectCity;

  /// No description provided for @analyzerResultsTitle.
  ///
  /// In en, this message translates to:
  /// **'ANALYSIS RESULTS'**
  String get analyzerResultsTitle;

  /// No description provided for @scoreCompatibility.
  ///
  /// In en, this message translates to:
  /// **'Compatibility Rate'**
  String get scoreCompatibility;

  /// No description provided for @scoreGoldenSeal.
  ///
  /// In en, this message translates to:
  /// **'Golden Ratio Seal'**
  String get scoreGoldenSeal;

  /// No description provided for @scoreVitality.
  ///
  /// In en, this message translates to:
  /// **'Relationship Vitality'**
  String get scoreVitality;

  /// No description provided for @scoreFlow.
  ///
  /// In en, this message translates to:
  /// **'Natural Flow'**
  String get scoreFlow;

  /// No description provided for @scorePotentialArea.
  ///
  /// In en, this message translates to:
  /// **'Potential Area'**
  String get scorePotentialArea;

  /// No description provided for @scoreAnalysisType.
  ///
  /// In en, this message translates to:
  /// **'Analysis Type'**
  String get scoreAnalysisType;

  /// No description provided for @scoreBirthChart.
  ///
  /// In en, this message translates to:
  /// **'Birth Chart'**
  String get scoreBirthChart;

  /// No description provided for @scoreDetectedArea.
  ///
  /// In en, this message translates to:
  /// **'Detected area'**
  String get scoreDetectedArea;

  /// No description provided for @scorePotentialTalent.
  ///
  /// In en, this message translates to:
  /// **'Potential & Talent'**
  String get scorePotentialTalent;

  /// No description provided for @torkLow.
  ///
  /// In en, this message translates to:
  /// **'Low energy — Relationship passive, joint activities needed to revive it'**
  String get torkLow;

  /// No description provided for @torkMid.
  ///
  /// In en, this message translates to:
  /// **'Medium level — Active but with ups and downs, can be balanced with communication'**
  String get torkMid;

  /// No description provided for @torkHigh.
  ///
  /// In en, this message translates to:
  /// **'High vitality — A dynamic and passionate bond, in constant interaction'**
  String get torkHigh;

  /// No description provided for @fraktalLow.
  ///
  /// In en, this message translates to:
  /// **'Difficult flow — Effort needed to harmonize, differences dominate'**
  String get fraktalLow;

  /// No description provided for @fraktalMid.
  ///
  /// In en, this message translates to:
  /// **'Medium flow — Fluctuations even though harmony is sometimes achieved'**
  String get fraktalMid;

  /// No description provided for @fraktalHigh.
  ///
  /// In en, this message translates to:
  /// **'Natural resonance — You understand each other easily, intuitive harmony'**
  String get fraktalHigh;

  /// No description provided for @loadingSky.
  ///
  /// In en, this message translates to:
  /// **'Analyzing your stellar bond...'**
  String get loadingSky;

  /// No description provided for @errorTryAgain.
  ///
  /// In en, this message translates to:
  /// **'Analysis could not be completed. Please check your information and try again.'**
  String get errorTryAgain;

  /// No description provided for @analyzerSidebarTagline.
  ///
  /// In en, this message translates to:
  /// **'FAST — Stellar Bond Analysis'**
  String get analyzerSidebarTagline;

  /// No description provided for @analyzerSidebarVersion.
  ///
  /// In en, this message translates to:
  /// **'Version 4.0 | 21-Year Cycle'**
  String get analyzerSidebarVersion;

  /// No description provided for @analyzerHeaderDesc.
  ///
  /// In en, this message translates to:
  /// **'Relative charts are a method developed by Fatih Asartepe by running existing charts on a different space plane with vector calculations. It is natural and normal that the results will not be the same as those in your natal chart.'**
  String get analyzerHeaderDesc;

  /// No description provided for @analyzerFeaturesEs1.
  ///
  /// In en, this message translates to:
  /// **'Couple chart & synastry planetary positions'**
  String get analyzerFeaturesEs1;

  /// No description provided for @analyzerFeaturesEs2.
  ///
  /// In en, this message translates to:
  /// **'21-year celestial cycle flow (yearly/monthly/daily)'**
  String get analyzerFeaturesEs2;

  /// No description provided for @analyzerFeaturesEs3.
  ///
  /// In en, this message translates to:
  /// **'Composite chart & common identity analysis'**
  String get analyzerFeaturesEs3;

  /// No description provided for @analyzerFeaturesEs4.
  ///
  /// In en, this message translates to:
  /// **'Planetary aspects, seals & celestial contract'**
  String get analyzerFeaturesEs4;

  /// No description provided for @analyzerFeaturesEs5.
  ///
  /// In en, this message translates to:
  /// **'Binary relationship alchemy, karmic bond & healing prescriptions'**
  String get analyzerFeaturesEs5;

  /// No description provided for @analyzerFeaturesEs6.
  ///
  /// In en, this message translates to:
  /// **'Astrocartography global city scan'**
  String get analyzerFeaturesEs6;

  /// No description provided for @analyzerFeaturesEs7.
  ///
  /// In en, this message translates to:
  /// **'6-month sky flow & station analysis'**
  String get analyzerFeaturesEs7;

  /// No description provided for @analyzerFeaturesEs8.
  ///
  /// In en, this message translates to:
  /// **'Arabic points radar, celestial time flow'**
  String get analyzerFeaturesEs8;

  /// No description provided for @analyzerFeaturesEs9.
  ///
  /// In en, this message translates to:
  /// **'Karmic house sealing & asteroid interactions'**
  String get analyzerFeaturesEs9;

  /// No description provided for @analyzerFeaturesEs10.
  ///
  /// In en, this message translates to:
  /// **'Full PDF report (unlimited download right)'**
  String get analyzerFeaturesEs10;

  /// No description provided for @analyzerFeaturesEb1.
  ///
  /// In en, this message translates to:
  /// **'Parent-child stellar bond & synastry analysis'**
  String get analyzerFeaturesEb1;

  /// No description provided for @analyzerFeaturesEb2.
  ///
  /// In en, this message translates to:
  /// **'Composite chart: common soul & family identity'**
  String get analyzerFeaturesEb2;

  /// No description provided for @analyzerFeaturesEb3.
  ///
  /// In en, this message translates to:
  /// **'Child\'s potential & talent chart (7 areas)'**
  String get analyzerFeaturesEb3;

  /// No description provided for @analyzerFeaturesEb4.
  ///
  /// In en, this message translates to:
  /// **'Development periods calendar & growth cycles'**
  String get analyzerFeaturesEb4;

  /// No description provided for @analyzerFeaturesEb5.
  ///
  /// In en, this message translates to:
  /// **'Yearly/monthly/daily child development flow'**
  String get analyzerFeaturesEb5;

  /// No description provided for @analyzerFeaturesEb6.
  ///
  /// In en, this message translates to:
  /// **'Career guidance & talent simulation'**
  String get analyzerFeaturesEb6;

  /// No description provided for @analyzerFeaturesEb7.
  ///
  /// In en, this message translates to:
  /// **'Arabic points bond analysis & celestial station'**
  String get analyzerFeaturesEb7;

  /// No description provided for @analyzerFeaturesEb8.
  ///
  /// In en, this message translates to:
  /// **'Healing prescriptions, support areas & asteroid effects'**
  String get analyzerFeaturesEb8;

  /// No description provided for @analyzerFeaturesEb9.
  ///
  /// In en, this message translates to:
  /// **'Planetary aspects, seals & astrocartography'**
  String get analyzerFeaturesEb9;

  /// No description provided for @analyzerFeaturesEb10.
  ///
  /// In en, this message translates to:
  /// **'Celestial time flow (21-year development path)'**
  String get analyzerFeaturesEb10;

  /// No description provided for @analyzerFeaturesEb11.
  ///
  /// In en, this message translates to:
  /// **'Full PDF report (unlimited download right)'**
  String get analyzerFeaturesEb11;

  /// No description provided for @analyzerFeaturesPy1.
  ///
  /// In en, this message translates to:
  /// **'Planetary positions & natal chart analysis'**
  String get analyzerFeaturesPy1;

  /// No description provided for @analyzerFeaturesPy2.
  ///
  /// In en, this message translates to:
  /// **'Potential and talent area detection'**
  String get analyzerFeaturesPy2;

  /// No description provided for @analyzerFeaturesPy3.
  ///
  /// In en, this message translates to:
  /// **'Career guidance recommendations'**
  String get analyzerFeaturesPy3;

  /// No description provided for @analyzerCalc.
  ///
  /// In en, this message translates to:
  /// **'Calculate'**
  String get analyzerCalc;

  /// No description provided for @analyzerLoadWorldMap.
  ///
  /// In en, this message translates to:
  /// **'Load World Map'**
  String get analyzerLoadWorldMap;

  /// No description provided for @analyzerPdfReport.
  ///
  /// In en, this message translates to:
  /// **'Download PDF Report'**
  String get analyzerPdfReport;

  /// No description provided for @analyzerPdfPotential.
  ///
  /// In en, this message translates to:
  /// **'Download Potential PDF'**
  String get analyzerPdfPotential;

  /// No description provided for @analyzerPdfNatal.
  ///
  /// In en, this message translates to:
  /// **'Download Natal PDF Report'**
  String get analyzerPdfNatal;

  /// No description provided for @analyzerChartNotReady.
  ///
  /// In en, this message translates to:
  /// **'This chart has not been created yet'**
  String get analyzerChartNotReady;

  /// No description provided for @analyzerClick.
  ///
  /// In en, this message translates to:
  /// **'tap →'**
  String get analyzerClick;

  /// No description provided for @analyzerCloseHint.
  ///
  /// In en, this message translates to:
  /// **'tap again to close'**
  String get analyzerCloseHint;

  /// No description provided for @analyzerPdfDownloaded.
  ///
  /// In en, this message translates to:
  /// **'PDF downloaded: {path}'**
  String analyzerPdfDownloaded(Object path);

  /// No description provided for @analyzerPdfError.
  ///
  /// In en, this message translates to:
  /// **'PDF download error: {error}'**
  String analyzerPdfError(Object error);

  /// No description provided for @analyzerPdfNotFound.
  ///
  /// In en, this message translates to:
  /// **'PDF not found ({code})'**
  String analyzerPdfNotFound(Object code);

  /// No description provided for @analyzerSectionKarmikHouse.
  ///
  /// In en, this message translates to:
  /// **'Karmic House Transfers'**
  String get analyzerSectionKarmikHouse;

  /// No description provided for @analyzerSectionRelativeClimate.
  ///
  /// In en, this message translates to:
  /// **'Relative Climate'**
  String get analyzerSectionRelativeClimate;

  /// No description provided for @analyzerSectionProgressionNatal.
  ///
  /// In en, this message translates to:
  /// **'Secondary Progression — Life Flow'**
  String get analyzerSectionProgressionNatal;

  /// No description provided for @analyzerSectionProgressionRelation.
  ///
  /// In en, this message translates to:
  /// **'Secondary Progression — Relationship Flow'**
  String get analyzerSectionProgressionRelation;

  /// No description provided for @analyzerSectionWeatherNatal.
  ///
  /// In en, this message translates to:
  /// **'Moon Transit Sky Flow — 3 Days'**
  String get analyzerSectionWeatherNatal;

  /// No description provided for @analyzerSectionWeather.
  ///
  /// In en, this message translates to:
  /// **'3-Day Sky Flow'**
  String get analyzerSectionWeather;

  /// No description provided for @analyzerSectionTimeMachine.
  ///
  /// In en, this message translates to:
  /// **'Celestial Time Flow (21 Years)'**
  String get analyzerSectionTimeMachine;

  /// No description provided for @analyzerSectionSeals.
  ///
  /// In en, this message translates to:
  /// **'Star Seals'**
  String get analyzerSectionSeals;

  /// No description provided for @analyzerSectionArabic.
  ///
  /// In en, this message translates to:
  /// **'Arabic Points'**
  String get analyzerSectionArabic;

  /// No description provided for @analyzerSectionArabicBonds.
  ///
  /// In en, this message translates to:
  /// **'Arabic Point Synastry Bonds'**
  String get analyzerSectionArabicBonds;

  /// No description provided for @analyzerSectionLifeAreas.
  ///
  /// In en, this message translates to:
  /// **'Life Areas Analysis'**
  String get analyzerSectionLifeAreas;

  /// No description provided for @analyzerSectionSabian.
  ///
  /// In en, this message translates to:
  /// **'Sabian Symbols'**
  String get analyzerSectionSabian;

  /// No description provided for @analyzerSectionSolarReturn.
  ///
  /// In en, this message translates to:
  /// **'Solar Return — Yearly Cycle'**
  String get analyzerSectionSolarReturn;

  /// No description provided for @analyzerSectionLunarReturn.
  ///
  /// In en, this message translates to:
  /// **'Lunar Return — Monthly Cycle'**
  String get analyzerSectionLunarReturn;

  /// No description provided for @analyzerSectionMinorProgress.
  ///
  /// In en, this message translates to:
  /// **'Minor Progress — 3-Day Flow'**
  String get analyzerSectionMinorProgress;

  /// No description provided for @analyzerSectionChartComment.
  ///
  /// In en, this message translates to:
  /// **'Birth Chart Interpretation'**
  String get analyzerSectionChartComment;

  /// No description provided for @analyzerSectionHealing.
  ///
  /// In en, this message translates to:
  /// **'Healing Prescriptions'**
  String get analyzerSectionHealing;

  /// No description provided for @analyzerSectionHealingDetail.
  ///
  /// In en, this message translates to:
  /// **'Detailed Healing Prescriptions'**
  String get analyzerSectionHealingDetail;

  /// No description provided for @analyzerSectionAsteroids.
  ///
  /// In en, this message translates to:
  /// **'Asteroid Interactions'**
  String get analyzerSectionAsteroids;

  /// No description provided for @analyzerSectionAlternateUniverse.
  ///
  /// In en, this message translates to:
  /// **'Alternate Universe'**
  String get analyzerSectionAlternateUniverse;

  /// No description provided for @analyzerSectionAcg.
  ///
  /// In en, this message translates to:
  /// **'Astrocartography & Global Star Compass'**
  String get analyzerSectionAcg;

  /// No description provided for @analyzerSectionPotential.
  ///
  /// In en, this message translates to:
  /// **'Potential and Talent Areas{isNatal}'**
  String analyzerSectionPotential(Object isNatal);

  /// No description provided for @analyzerSectionProfession.
  ///
  /// In en, this message translates to:
  /// **'Career Guidance Recommendations'**
  String get analyzerSectionProfession;

  /// No description provided for @analyzerChartsTitle.
  ///
  /// In en, this message translates to:
  /// **'Charts'**
  String get analyzerChartsTitle;

  /// No description provided for @analyzerReportTitle.
  ///
  /// In en, this message translates to:
  /// **'Report'**
  String get analyzerReportTitle;

  /// No description provided for @analyzerProgressionYear.
  ///
  /// In en, this message translates to:
  /// **'Progression Year: {year}'**
  String analyzerProgressionYear(Object year);

  /// No description provided for @analyzerMoon.
  ///
  /// In en, this message translates to:
  /// **'Moon'**
  String get analyzerMoon;

  /// No description provided for @analyzerSun.
  ///
  /// In en, this message translates to:
  /// **'Sun'**
  String get analyzerSun;

  /// No description provided for @analyzerTotalAspects.
  ///
  /// In en, this message translates to:
  /// **'A total of {count} progressed aspects were detected.'**
  String analyzerTotalAspects(Object count);

  /// No description provided for @analyzerSimulationRenewed.
  ///
  /// In en, this message translates to:
  /// **'Simulation: analysis renewed at {city} coordinates'**
  String analyzerSimulationRenewed(Object city);

  /// No description provided for @analyzerSimulationScan.
  ///
  /// In en, this message translates to:
  /// **'Star Compass Scan — 15,000+ cities analyzed. Tap the photo to open the Wikipedia page, use the ↻ button to renew the analysis at that location.'**
  String get analyzerSimulationScan;

  /// No description provided for @analyzerAstroHint.
  ///
  /// In en, this message translates to:
  /// **'Select a different location to see the energies of that region (Money, Peace, Passion, Crisis).'**
  String get analyzerAstroHint;

  /// No description provided for @analyzerStarScan.
  ///
  /// In en, this message translates to:
  /// **'Star Compass Scan'**
  String get analyzerStarScan;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'tr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'tr':
      return AppLocalizationsTr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
