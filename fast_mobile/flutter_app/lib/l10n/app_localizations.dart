import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_es.dart';
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
    Locale('es'),
    Locale('tr'),
  ];

  /// No description provided for @editorPinchHint.
  ///
  /// In en, this message translates to:
  /// **'Pinch to zoom • twist to rotate'**
  String get editorPinchHint;

  /// No description provided for @storyDelete.
  ///
  /// In en, this message translates to:
  /// **'Delete story'**
  String get storyDelete;

  /// No description provided for @storyDeleteConfirm.
  ///
  /// In en, this message translates to:
  /// **'This story will be permanently deleted.'**
  String get storyDeleteConfirm;

  /// No description provided for @storyDeleteDone.
  ///
  /// In en, this message translates to:
  /// **'Story deleted'**
  String get storyDeleteDone;

  /// No description provided for @profileTabPosts.
  ///
  /// In en, this message translates to:
  /// **'POSTS'**
  String get profileTabPosts;

  /// No description provided for @profileTabReels.
  ///
  /// In en, this message translates to:
  /// **'REELS'**
  String get profileTabReels;

  /// No description provided for @profileLoginNeeded.
  ///
  /// In en, this message translates to:
  /// **'Log in to see your profile'**
  String get profileLoginNeeded;

  /// No description provided for @socialErrorNetwork.
  ///
  /// In en, this message translates to:
  /// **'No connection'**
  String get socialErrorNetwork;

  /// No description provided for @socialErrorServer.
  ///
  /// In en, this message translates to:
  /// **'Could not reach the server'**
  String get socialErrorServer;

  /// No description provided for @socialErrorHint.
  ///
  /// In en, this message translates to:
  /// **'The community feed could not be loaded. Check your internet connection and try again.'**
  String get socialErrorHint;

  /// No description provided for @socialRetry.
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get socialRetry;

  /// No description provided for @dmBlocked.
  ///
  /// In en, this message translates to:
  /// **'You cannot message this user'**
  String get dmBlocked;

  /// No description provided for @accountDelete.
  ///
  /// In en, this message translates to:
  /// **'Delete my account and data'**
  String get accountDelete;

  /// No description provided for @accountDeleteTitle.
  ///
  /// In en, this message translates to:
  /// **'Delete account'**
  String get accountDeleteTitle;

  /// No description provided for @accountDeleteConfirm.
  ///
  /// In en, this message translates to:
  /// **'Your account, all your posts, comments, messages and saved people will be permanently deleted. This cannot be undone.'**
  String get accountDeleteConfirm;

  /// No description provided for @accountDeleteConfirmBtn.
  ///
  /// In en, this message translates to:
  /// **'Delete permanently'**
  String get accountDeleteConfirmBtn;

  /// No description provided for @accountDeleteDone.
  ///
  /// In en, this message translates to:
  /// **'Your account and data were deleted'**
  String get accountDeleteDone;

  /// No description provided for @accountDeleteFailed.
  ///
  /// In en, this message translates to:
  /// **'Could not delete the account. Please try again later.'**
  String get accountDeleteFailed;

  /// No description provided for @fileTooLarge.
  ///
  /// In en, this message translates to:
  /// **'File is too large. Please pick an image under 5 MB.'**
  String get fileTooLarge;

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'Holavon'**
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
  /// **'Discover the depths of your relationship, your child\'s potential, or your own talents with Holavon.'**
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
  /// **'Explore every dimension of astrological analysis with Holavon'**
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
  /// **'Try Analysis, Horary and Social for free'**
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

  /// No description provided for @planFreeFeat6.
  ///
  /// In en, this message translates to:
  /// **'Horary: 3 questions per day'**
  String get planFreeFeat6;

  /// No description provided for @planFreeFeat7.
  ///
  /// In en, this message translates to:
  /// **'Social feed, stories and DMs'**
  String get planFreeFeat7;

  /// No description provided for @planFreeFeat8.
  ///
  /// In en, this message translates to:
  /// **'Profile and saved people'**
  String get planFreeFeat8;

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

  /// No description provided for @planFreeDisabled6.
  ///
  /// In en, this message translates to:
  /// **'Unlimited Horary'**
  String get planFreeDisabled6;

  /// No description provided for @planFreeDisabled7.
  ///
  /// In en, this message translates to:
  /// **'Gold Pro badge'**
  String get planFreeDisabled7;

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

  /// No description provided for @planProMonthlyDesc.
  ///
  /// In en, this message translates to:
  /// **'Monthly Pro membership'**
  String get planProMonthlyDesc;

  /// No description provided for @planProYearlyDesc.
  ///
  /// In en, this message translates to:
  /// **'Yearly Pro membership'**
  String get planProYearlyDesc;

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
  /// **'1 year update right'**
  String get planProFeat3;

  /// No description provided for @planProFeat4.
  ///
  /// In en, this message translates to:
  /// **'Priority support'**
  String get planProFeat4;

  /// No description provided for @planProFeat8.
  ///
  /// In en, this message translates to:
  /// **'Unlimited Horary questions'**
  String get planProFeat8;

  /// No description provided for @planProFeat9.
  ///
  /// In en, this message translates to:
  /// **'Gold Pro badge on your social profile'**
  String get planProFeat9;

  /// No description provided for @planProFeat10.
  ///
  /// In en, this message translates to:
  /// **'Three apps in one subscription: Analysis + Horary + Social'**
  String get planProFeat10;

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
  /// **'Holavon — stellar bond analysis with the Fatih Asartepe Synastry Technique (FAST).'**
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
  /// **'© 2026 Holavon®. All rights reserved.'**
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

  /// No description provided for @spanish.
  ///
  /// In en, this message translates to:
  /// **'Spanish'**
  String get spanish;

  /// No description provided for @homeTitle.
  ///
  /// In en, this message translates to:
  /// **'Holavon\nAstrology'**
  String get homeTitle;

  /// No description provided for @homeSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Holavon — Stellar Bond Analysis System'**
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
  /// **'Holavon — Stellar Bond Analysis'**
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

  /// No description provided for @analyzerPdfSuccess.
  ///
  /// In en, this message translates to:
  /// **'Report downloaded and opened.'**
  String get analyzerPdfSuccess;

  /// No description provided for @analyzerPdfPreparing.
  ///
  /// In en, this message translates to:
  /// **'Preparing your report…'**
  String get analyzerPdfPreparing;

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
  /// **'Short-Term Progression — 3-Day Flow'**
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

  /// No description provided for @analyzerSectionSinastriNarrative.
  ///
  /// In en, this message translates to:
  /// **'Synastry Narrative'**
  String get analyzerSectionSinastriNarrative;

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

  /// No description provided for @themePickerTitle.
  ///
  /// In en, this message translates to:
  /// **'Select Theme'**
  String get themePickerTitle;

  /// No description provided for @themeAppearanceTitle.
  ///
  /// In en, this message translates to:
  /// **'Appearance'**
  String get themeAppearanceTitle;

  /// No description provided for @themeAppearanceHint.
  ///
  /// In en, this message translates to:
  /// **'Choose the app color palette'**
  String get themeAppearanceHint;

  /// No description provided for @proBadgeTooltip.
  ///
  /// In en, this message translates to:
  /// **'Holavon Pro member'**
  String get proBadgeTooltip;

  /// No description provided for @themePaletteDark.
  ///
  /// In en, this message translates to:
  /// **'Purple (Dark)'**
  String get themePaletteDark;

  /// No description provided for @themePaletteLight.
  ///
  /// In en, this message translates to:
  /// **'Soft Cream (Light)'**
  String get themePaletteLight;

  /// No description provided for @themePaletteSpain.
  ///
  /// In en, this message translates to:
  /// **'Spain Red (Dark)'**
  String get themePaletteSpain;

  /// No description provided for @themePaletteArgentina.
  ///
  /// In en, this message translates to:
  /// **'Argentina Blue (Light)'**
  String get themePaletteArgentina;

  /// No description provided for @chartTabSituaA.
  ///
  /// In en, this message translates to:
  /// **'Chart A'**
  String get chartTabSituaA;

  /// No description provided for @chartTabSituaB.
  ///
  /// In en, this message translates to:
  /// **'Chart B'**
  String get chartTabSituaB;

  /// No description provided for @chartTabFrekans.
  ///
  /// In en, this message translates to:
  /// **'Frequency Map'**
  String get chartTabFrekans;

  /// No description provided for @chartTabComposite.
  ///
  /// In en, this message translates to:
  /// **'Composite Map'**
  String get chartTabComposite;

  /// No description provided for @chartTabAciGridi.
  ///
  /// In en, this message translates to:
  /// **'Aspect Grid'**
  String get chartTabAciGridi;

  /// No description provided for @chartTabArapNoktalari.
  ///
  /// In en, this message translates to:
  /// **'Arabic Parts'**
  String get chartTabArapNoktalari;

  /// No description provided for @analyzerReportTitle.
  ///
  /// In en, this message translates to:
  /// **'Report'**
  String get analyzerReportTitle;

  /// No description provided for @exitToMenu.
  ///
  /// In en, this message translates to:
  /// **'Back to Menu'**
  String get exitToMenu;

  /// No description provided for @exitFromAnalysis.
  ///
  /// In en, this message translates to:
  /// **'Exit Analysis'**
  String get exitFromAnalysis;

  /// No description provided for @newAnalysis.
  ///
  /// In en, this message translates to:
  /// **'New Analysis'**
  String get newAnalysis;

  /// No description provided for @pdfPaymentRequired.
  ///
  /// In en, this message translates to:
  /// **'This book requires a subscription or a one-time purchase.'**
  String get pdfPaymentRequired;

  /// No description provided for @pdfPreparingNote.
  ///
  /// In en, this message translates to:
  /// **'Your report is being prepared, this may take a while.'**
  String get pdfPreparingNote;

  /// No description provided for @astrokartografiSubscribe.
  ///
  /// In en, this message translates to:
  /// **'Subscribe'**
  String get astrokartografiSubscribe;

  /// No description provided for @astrokartografiHint.
  ///
  /// In en, this message translates to:
  /// **'World map view is included with subscription.'**
  String get astrokartografiHint;

  /// No description provided for @subscribeSuccess.
  ///
  /// In en, this message translates to:
  /// **'Your subscription is active. Welcome!'**
  String get subscribeSuccess;

  /// No description provided for @subscribeCancelled.
  ///
  /// In en, this message translates to:
  /// **'Subscription cancelled.'**
  String get subscribeCancelled;

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

  /// No description provided for @errorTitle.
  ///
  /// In en, this message translates to:
  /// **'Error'**
  String get errorTitle;

  /// No description provided for @unknownError.
  ///
  /// In en, this message translates to:
  /// **'Unknown error'**
  String get unknownError;

  /// No description provided for @retryButton.
  ///
  /// In en, this message translates to:
  /// **'Try Again'**
  String get retryButton;

  /// No description provided for @imageLoadError.
  ///
  /// In en, this message translates to:
  /// **'Image could not be loaded'**
  String get imageLoadError;

  /// No description provided for @chooseLanguage.
  ///
  /// In en, this message translates to:
  /// **'Choose your language'**
  String get chooseLanguage;

  /// No description provided for @chooseLanguageSub.
  ///
  /// In en, this message translates to:
  /// **'Dilinizi seçin'**
  String get chooseLanguageSub;

  /// No description provided for @analyzerParentRole.
  ///
  /// In en, this message translates to:
  /// **'Parent Role'**
  String get analyzerParentRole;

  /// No description provided for @analyzerParentNameRequired.
  ///
  /// In en, this message translates to:
  /// **'Enter the parent\'s name'**
  String get analyzerParentNameRequired;

  /// No description provided for @analyzerLocationLoading.
  ///
  /// In en, this message translates to:
  /// **'Fetching location...'**
  String get analyzerLocationLoading;

  /// No description provided for @analyzerPersonA.
  ///
  /// In en, this message translates to:
  /// **'Chart A'**
  String get analyzerPersonA;

  /// No description provided for @analyzerPersonB.
  ///
  /// In en, this message translates to:
  /// **'Chart B'**
  String get analyzerPersonB;

  /// No description provided for @scoreVitalityTork.
  ///
  /// In en, this message translates to:
  /// **'Relationship Vitality (Torque)'**
  String get scoreVitalityTork;

  /// No description provided for @scoreFlowFraktal.
  ///
  /// In en, this message translates to:
  /// **'Natural Flow (Fractal)'**
  String get scoreFlowFraktal;

  /// No description provided for @scoreDetailTitle.
  ///
  /// In en, this message translates to:
  /// **'SCORE ANALYSIS DETAILS'**
  String get scoreDetailTitle;

  /// No description provided for @progressionTitle.
  ///
  /// In en, this message translates to:
  /// **'Secondary Progression'**
  String get progressionTitle;

  /// No description provided for @weatherTitle.
  ///
  /// In en, this message translates to:
  /// **'Sky Flow (3 Days)'**
  String get weatherTitle;

  /// No description provided for @timeMachineTitle.
  ///
  /// In en, this message translates to:
  /// **'Celestial Time Flow (21 Years)'**
  String get timeMachineTitle;

  /// No description provided for @astrokartografiTitle.
  ///
  /// In en, this message translates to:
  /// **'Astrocartography'**
  String get astrokartografiTitle;

  /// No description provided for @alternateUniverseScores.
  ///
  /// In en, this message translates to:
  /// **'Alternate Universe Scores'**
  String get alternateUniverseScores;

  /// No description provided for @cityCompassTitle.
  ///
  /// In en, this message translates to:
  /// **'🌍 City Compass'**
  String get cityCompassTitle;

  /// No description provided for @downloadPdfButton.
  ///
  /// In en, this message translates to:
  /// **'📥 Download PDF ({mod})'**
  String downloadPdfButton(Object mod);

  /// No description provided for @bookIliski.
  ///
  /// In en, this message translates to:
  /// **'Relationship Book'**
  String get bookIliski;

  /// No description provided for @bookEbeveyn.
  ///
  /// In en, this message translates to:
  /// **'Parenting Book'**
  String get bookEbeveyn;

  /// No description provided for @bookEl.
  ///
  /// In en, this message translates to:
  /// **'Handbook'**
  String get bookEl;

  /// No description provided for @downloadBookButton.
  ///
  /// In en, this message translates to:
  /// **'📥 Download {book}'**
  String downloadBookButton(Object book);

  /// No description provided for @pdfAlreadyOwnedTitle.
  ///
  /// In en, this message translates to:
  /// **'Already purchased'**
  String get pdfAlreadyOwnedTitle;

  /// No description provided for @pdfAlreadyOwnedBody.
  ///
  /// In en, this message translates to:
  /// **'This book appears to be already purchased on your Google Play account. Sign in with the account you purchased with, then try downloading again.'**
  String get pdfAlreadyOwnedBody;

  /// No description provided for @analyzerYearLine.
  ///
  /// In en, this message translates to:
  /// **'Year: {year}'**
  String analyzerYearLine(Object year);

  /// No description provided for @analyzerMoonSun.
  ///
  /// In en, this message translates to:
  /// **'🌙 Moon: {moon} | ☀️ Sun: {sun}'**
  String analyzerMoonSun(Object moon, Object sun);

  /// No description provided for @analyzerMoonSunHouse.
  ///
  /// In en, this message translates to:
  /// **'🌙 Moon: {moon} ({house}. House) | ☀️ Sun: {sun}'**
  String analyzerMoonSunHouse(Object house, Object moon, Object sun);

  /// No description provided for @analyzerMoonTransitLine.
  ///
  /// In en, this message translates to:
  /// **'🌙 Moon {sign} — {house}. House ({degree}°)'**
  String analyzerMoonTransitLine(Object degree, Object house, Object sign);

  /// No description provided for @analyzerAspectOrb.
  ///
  /// In en, this message translates to:
  /// **'{aspect} — {type}° Aspect (Orb: {orb})'**
  String analyzerAspectOrb(Object aspect, Object orb, Object type);

  /// No description provided for @analyzerScorePoints.
  ///
  /// In en, this message translates to:
  /// **'{points} points ({percent}%)'**
  String analyzerScorePoints(Object percent, Object points);

  /// No description provided for @analyzerPotentialChildDesc.
  ///
  /// In en, this message translates to:
  /// **'Natural talent, potential areas and career directions detected from the planetary aspects in the child\'s chart.'**
  String get analyzerPotentialChildDesc;

  /// No description provided for @analyzerPotentialSelfDesc.
  ///
  /// In en, this message translates to:
  /// **'Natural talent, potential areas and career directions detected from the planetary aspects in your chart.'**
  String get analyzerPotentialSelfDesc;

  /// No description provided for @analyzerPotentialTop5Hint.
  ///
  /// In en, this message translates to:
  /// **'💡 Only the first 5 talent areas are shown in the browser. All areas are in the PDF report.'**
  String get analyzerPotentialTop5Hint;

  /// No description provided for @analyzerPotentialAllPdf.
  ///
  /// In en, this message translates to:
  /// **'All potential and talent areas are detailed in your PDF report.'**
  String get analyzerPotentialAllPdf;

  /// No description provided for @analyzerProfessionChildDesc.
  ///
  /// In en, this message translates to:
  /// **'Career fields the child is inclined toward, determined by the synthesis of their potential and talent areas.'**
  String get analyzerProfessionChildDesc;

  /// No description provided for @analyzerProfessionSelfDesc.
  ///
  /// In en, this message translates to:
  /// **'Career fields you are inclined toward, determined by the synthesis of your potential and talent areas.'**
  String get analyzerProfessionSelfDesc;

  /// No description provided for @analyzerProfessionFullRanking.
  ///
  /// In en, this message translates to:
  /// **'💡 The full ranking is in the PDF report.'**
  String get analyzerProfessionFullRanking;

  /// No description provided for @analyzerProfessionScoringNote.
  ///
  /// In en, this message translates to:
  /// **'Scoring: Calculated using planet-sign matches, aspect type, orb proximity, legend boost, MC bonus and asteroid support.'**
  String get analyzerProfessionScoringNote;

  /// No description provided for @analyzerProfessionPdfHint.
  ///
  /// In en, this message translates to:
  /// **'Check your PDF report for a detailed explanation.'**
  String get analyzerProfessionPdfHint;

  /// No description provided for @analyzerArabicIntro.
  ///
  /// In en, this message translates to:
  /// **'Arabic Points represent cosmic points in astrology. The relationship-focused point positions of both people.'**
  String get analyzerArabicIntro;

  /// No description provided for @analyzerArabicPdfHint.
  ///
  /// In en, this message translates to:
  /// **'💡 Detailed sign and house interpretations are in your PDF report.'**
  String get analyzerArabicPdfHint;

  /// No description provided for @analyzerLifeAreasIntro.
  ///
  /// In en, this message translates to:
  /// **'Comprehensive category cards for your entire chart — personal analysis and recommendations for each area.'**
  String get analyzerLifeAreasIntro;

  /// No description provided for @analyzerSabianIntro.
  ///
  /// In en, this message translates to:
  /// **'Sabian symbols and interpretations based on the degrees your planets occupy.'**
  String get analyzerSabianIntro;

  /// No description provided for @analyzerMinorProgress6Month.
  ///
  /// In en, this message translates to:
  /// **'📄 A comprehensive 6-month Short-Term Progression report is presented in the PDF.'**
  String get analyzerMinorProgress6Month;

  /// No description provided for @analyzerChartCommentIntro.
  ///
  /// In en, this message translates to:
  /// **'A holistic chart analysis covering planetary positions, aspect patterns, Arabic points and asteroid themes.'**
  String get analyzerChartCommentIntro;

  /// No description provided for @analyzerHealingIntro.
  ///
  /// In en, this message translates to:
  /// **'Personal healing and balance recommendations based on the planetary positions in your birth chart.'**
  String get analyzerHealingIntro;

  /// No description provided for @analyzerHealingDetailIntro.
  ///
  /// In en, this message translates to:
  /// **'Special remediation techniques and recommendations for challenging aspects and planets in detriment/fall.'**
  String get analyzerHealingDetailIntro;

  /// No description provided for @analyzerAsteroidsIntro.
  ///
  /// In en, this message translates to:
  /// **'Cross-aspect themes of the Juno, Ceres, Pallas, Vesta, Eros, Psyche, Sappho and Amor asteroids.'**
  String get analyzerAsteroidsIntro;

  /// No description provided for @analyzerAsteroidsOrbHint.
  ///
  /// In en, this message translates to:
  /// **'💡 Contacts within the 0-5° orb range are shown.'**
  String get analyzerAsteroidsOrbHint;

  /// No description provided for @analyzerAsteroidsAllPdf.
  ///
  /// In en, this message translates to:
  /// **'All asteroid interactions are detailed in your PDF report.'**
  String get analyzerAsteroidsAllPdf;

  /// No description provided for @analyzerAcgGlobalIntro.
  ///
  /// In en, this message translates to:
  /// **'An interactive map showing where your birth chart planets peak on Earth and a star compatibility scan across 15,000+ cities.'**
  String get analyzerAcgGlobalIntro;

  /// No description provided for @simCatWealth.
  ///
  /// In en, this message translates to:
  /// **'Money & Career'**
  String get simCatWealth;

  /// No description provided for @simCatPeace.
  ///
  /// In en, this message translates to:
  /// **'Peace & Serenity'**
  String get simCatPeace;

  /// No description provided for @simCatPassion.
  ///
  /// In en, this message translates to:
  /// **'Passion & Love'**
  String get simCatPassion;

  /// No description provided for @simCatCrisis.
  ///
  /// In en, this message translates to:
  /// **'Crisis & Challenge'**
  String get simCatCrisis;

  /// No description provided for @astroScoreMoney.
  ///
  /// In en, this message translates to:
  /// **'💰 Money'**
  String get astroScoreMoney;

  /// No description provided for @astroScorePeace.
  ///
  /// In en, this message translates to:
  /// **'☮️ Peace'**
  String get astroScorePeace;

  /// No description provided for @astroScorePassion.
  ///
  /// In en, this message translates to:
  /// **'🔥 Passion'**
  String get astroScorePassion;

  /// No description provided for @astroScoreCrisis.
  ///
  /// In en, this message translates to:
  /// **'⚡ Crisis'**
  String get astroScoreCrisis;

  /// No description provided for @astroBarMoney.
  ///
  /// In en, this message translates to:
  /// **'💰 Money & Career'**
  String get astroBarMoney;

  /// No description provided for @astroBarPeace.
  ///
  /// In en, this message translates to:
  /// **'🧘 Peace & Serenity'**
  String get astroBarPeace;

  /// No description provided for @astroBarPassion.
  ///
  /// In en, this message translates to:
  /// **'🔥 Passion & Love'**
  String get astroBarPassion;

  /// No description provided for @astroBarCrisis.
  ///
  /// In en, this message translates to:
  /// **'⚠️ Crisis & Challenge'**
  String get astroBarCrisis;

  /// No description provided for @scoreBondLabel.
  ///
  /// In en, this message translates to:
  /// **'Bond Score'**
  String get scoreBondLabel;

  /// No description provided for @warningTitle.
  ///
  /// In en, this message translates to:
  /// **'Important Notice'**
  String get warningTitle;

  /// No description provided for @warningBody.
  ///
  /// In en, this message translates to:
  /// **'The synastry work in this app is carried out with the vectorial transfer method developed by Karma Astrologer Fatih ASARTEPE and with meeting-date calibration. This is why the meeting or marriage date is requested instead of the birth times of the people, and the meeting or marriage place is requested instead of their birth places. The resulting charts will differ from natal charts, but they will give you incredible results for your life and your relationship.'**
  String get warningBody;

  /// No description provided for @warningAcknowledge.
  ///
  /// In en, this message translates to:
  /// **'I Understand'**
  String get warningAcknowledge;

  /// No description provided for @warningBack.
  ///
  /// In en, this message translates to:
  /// **'Back'**
  String get warningBack;

  /// No description provided for @loginNav.
  ///
  /// In en, this message translates to:
  /// **'Sign In'**
  String get loginNav;

  /// No description provided for @loginTitle.
  ///
  /// In en, this message translates to:
  /// **'Sign In'**
  String get loginTitle;

  /// No description provided for @loginSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Sign in to your account and access your saved people from any device.'**
  String get loginSubtitle;

  /// No description provided for @loginEmailLabel.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get loginEmailLabel;

  /// No description provided for @loginPasswordLabel.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get loginPasswordLabel;

  /// No description provided for @loginRemember.
  ///
  /// In en, this message translates to:
  /// **'Remember me'**
  String get loginRemember;

  /// No description provided for @loginForgot.
  ///
  /// In en, this message translates to:
  /// **'Forgot password?'**
  String get loginForgot;

  /// No description provided for @loginButton.
  ///
  /// In en, this message translates to:
  /// **'Sign In'**
  String get loginButton;

  /// No description provided for @signupButton.
  ///
  /// In en, this message translates to:
  /// **'Create Account'**
  String get signupButton;

  /// No description provided for @loginOr.
  ///
  /// In en, this message translates to:
  /// **'or'**
  String get loginOr;

  /// No description provided for @loginGoogle.
  ///
  /// In en, this message translates to:
  /// **'Continue with Google'**
  String get loginGoogle;

  /// No description provided for @loginFacebook.
  ///
  /// In en, this message translates to:
  /// **'Continue with Facebook'**
  String get loginFacebook;

  /// No description provided for @loginNoAccount.
  ///
  /// In en, this message translates to:
  /// **'Don\'t have an account? Sign up'**
  String get loginNoAccount;

  /// No description provided for @loginHaveAccount.
  ///
  /// In en, this message translates to:
  /// **'Already have an account? Sign in'**
  String get loginHaveAccount;

  /// No description provided for @loginGuest.
  ///
  /// In en, this message translates to:
  /// **'Continue as guest'**
  String get loginGuest;

  /// No description provided for @loginErrorGeneric.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Please try again.'**
  String get loginErrorGeneric;

  /// No description provided for @loginErrorInvalid.
  ///
  /// In en, this message translates to:
  /// **'Incorrect email or password.'**
  String get loginErrorInvalid;

  /// No description provided for @loginErrorExists.
  ///
  /// In en, this message translates to:
  /// **'This email is already registered.'**
  String get loginErrorExists;

  /// No description provided for @loginErrorDisabled.
  ///
  /// In en, this message translates to:
  /// **'Membership is not configured yet.'**
  String get loginErrorDisabled;

  /// No description provided for @loginSuccess.
  ///
  /// In en, this message translates to:
  /// **'Signed in successfully!'**
  String get loginSuccess;

  /// No description provided for @logoutButton.
  ///
  /// In en, this message translates to:
  /// **'Log Out'**
  String get logoutButton;

  /// No description provided for @profileTitle.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profileTitle;

  /// No description provided for @profileEmailLabel.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get profileEmailLabel;

  /// No description provided for @profileNameLabel.
  ///
  /// In en, this message translates to:
  /// **'Full Name'**
  String get profileNameLabel;

  /// No description provided for @profileSave.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get profileSave;

  /// No description provided for @profileChangePassword.
  ///
  /// In en, this message translates to:
  /// **'Change Password'**
  String get profileChangePassword;

  /// No description provided for @profileNewPassword.
  ///
  /// In en, this message translates to:
  /// **'New Password'**
  String get profileNewPassword;

  /// No description provided for @profilePasswordChanged.
  ///
  /// In en, this message translates to:
  /// **'Password updated.'**
  String get profilePasswordChanged;

  /// No description provided for @profileSaved.
  ///
  /// In en, this message translates to:
  /// **'Profile updated.'**
  String get profileSaved;

  /// No description provided for @peopleTitle.
  ///
  /// In en, this message translates to:
  /// **'Saved People'**
  String get peopleTitle;

  /// No description provided for @peopleEmpty.
  ///
  /// In en, this message translates to:
  /// **'You have no saved people yet. You can save a person from the analysis form.'**
  String get peopleEmpty;

  /// No description provided for @peopleFolderLabel.
  ///
  /// In en, this message translates to:
  /// **'Folder'**
  String get peopleFolderLabel;

  /// No description provided for @peopleFolderFamily.
  ///
  /// In en, this message translates to:
  /// **'My Family'**
  String get peopleFolderFamily;

  /// No description provided for @peopleFolderFriends.
  ///
  /// In en, this message translates to:
  /// **'My Friends'**
  String get peopleFolderFriends;

  /// No description provided for @peopleSave.
  ///
  /// In en, this message translates to:
  /// **'Save Person'**
  String get peopleSave;

  /// No description provided for @peopleSaved.
  ///
  /// In en, this message translates to:
  /// **'Person saved.'**
  String get peopleSaved;

  /// No description provided for @peopleDeleted.
  ///
  /// In en, this message translates to:
  /// **'Person deleted.'**
  String get peopleDeleted;

  /// No description provided for @peopleDelete.
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get peopleDelete;

  /// No description provided for @peopleSelect.
  ///
  /// In en, this message translates to:
  /// **'Select saved person'**
  String get peopleSelect;

  /// No description provided for @peopleLoginRequired.
  ///
  /// In en, this message translates to:
  /// **'Sign in to save a person.'**
  String get peopleLoginRequired;

  /// No description provided for @peopleSave1.
  ///
  /// In en, this message translates to:
  /// **'Save Person 1'**
  String get peopleSave1;

  /// No description provided for @peopleSave2.
  ///
  /// In en, this message translates to:
  /// **'Save Person 2'**
  String get peopleSave2;

  /// No description provided for @peopleNewFolder.
  ///
  /// In en, this message translates to:
  /// **'New Folder'**
  String get peopleNewFolder;

  /// No description provided for @peopleFolderNameHint.
  ///
  /// In en, this message translates to:
  /// **'New folder name'**
  String get peopleFolderNameHint;

  /// No description provided for @peopleCancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get peopleCancel;

  /// No description provided for @peopleNameRequired.
  ///
  /// In en, this message translates to:
  /// **'Enter a name'**
  String get peopleNameRequired;

  /// No description provided for @peopleBirthDateRequired.
  ///
  /// In en, this message translates to:
  /// **'Enter birth date'**
  String get peopleBirthDateRequired;

  /// No description provided for @peopleBirthTimeRequired.
  ///
  /// In en, this message translates to:
  /// **'Enter birth time'**
  String get peopleBirthTimeRequired;

  /// No description provided for @peopleFolderRequired.
  ///
  /// In en, this message translates to:
  /// **'Enter a folder name'**
  String get peopleFolderRequired;

  /// No description provided for @peopleApplyTo.
  ///
  /// In en, this message translates to:
  /// **'Apply person to'**
  String get peopleApplyTo;

  /// No description provided for @peopleApplyPerson1.
  ///
  /// In en, this message translates to:
  /// **'Person 1'**
  String get peopleApplyPerson1;

  /// No description provided for @peopleApplyPerson2.
  ///
  /// In en, this message translates to:
  /// **'Person 2'**
  String get peopleApplyPerson2;

  /// Relationship Scores
  ///
  /// In en, this message translates to:
  /// **'Relationship Scores'**
  String get modeAshTitle;

  /// No description provided for @modeAshDesc.
  ///
  /// In en, this message translates to:
  /// **'Vedic relationship compatibility scores (36 guna points)'**
  String get modeAshDesc;

  /// No description provided for @modeAshBadge.
  ///
  /// In en, this message translates to:
  /// **'Match'**
  String get modeAshBadge;

  /// Moon nakshatra compatibility (out of 36)
  ///
  /// In en, this message translates to:
  /// **'Moon nakshatra compatibility (out of 36)'**
  String get analyzerModeAshDesc;

  /// Relationship Scores measures the Moon nakshatra (pada) compatibility of two people out of 36 points. The Moon's position depends only on the moment of birth, so entering your birth city is enough — we calculate the correct time zone for you, including historical daylight saving. You can leave the birth time blank if you don't know it.
  ///
  /// In en, this message translates to:
  /// **'Relationship Scores measures the Moon nakshatra (pada) compatibility of two people out of 36 points. The Moon\'s position depends only on the moment of birth, so entering your birth city is enough — we calculate the correct time zone for you, including historical daylight saving. You can leave the birth time blank if you don\'t know it.'**
  String get ashExplainer;

  /// Time zone
  ///
  /// In en, this message translates to:
  /// **'Time zone'**
  String get ashUtcOffset;

  /// First person Moon
  ///
  /// In en, this message translates to:
  /// **'First person Moon'**
  String get ashPersonAMoon;

  /// Second person Moon
  ///
  /// In en, this message translates to:
  /// **'Second person Moon'**
  String get ashPersonBMoon;

  /// Moon Profiles
  ///
  /// In en, this message translates to:
  /// **'Moon Profiles'**
  String get ashMoonProfiles;

  /// Kootas (36 points)
  ///
  /// In en, this message translates to:
  /// **'Kootas (36 points)'**
  String get ashKootalar;

  /// Total Compatibility
  ///
  /// In en, this message translates to:
  /// **'Total Compatibility'**
  String get ashTotalScore;

  /// Warnings
  ///
  /// In en, this message translates to:
  /// **'Warnings'**
  String get ashWarnings;

  /// Calculated approximately because the birth time is unknown.
  ///
  /// In en, this message translates to:
  /// **'Calculated approximately because the birth time is unknown.'**
  String get ashApproximate;

  /// Varna
  ///
  /// In en, this message translates to:
  /// **'Varna'**
  String get ashVarna;

  /// Gana
  ///
  /// In en, this message translates to:
  /// **'Gana'**
  String get ashGana;

  /// Nadi
  ///
  /// In en, this message translates to:
  /// **'Nadi'**
  String get ashNadi;

  /// Very low
  ///
  /// In en, this message translates to:
  /// **'Very low'**
  String get ashLevelVeryLow;

  /// Low
  ///
  /// In en, this message translates to:
  /// **'Low'**
  String get ashLevelLow;

  /// Moderate
  ///
  /// In en, this message translates to:
  /// **'Moderate'**
  String get ashLevelMedium;

  /// High
  ///
  /// In en, this message translates to:
  /// **'High'**
  String get ashLevelHigh;

  /// No description provided for @ashTimeOptional.
  ///
  /// In en, this message translates to:
  /// **'Leave blank if you don\'t know the birth time — we use noon (12:00) and mark the result as approximate.'**
  String get ashTimeOptional;

  /// No description provided for @ashBirthCity1.
  ///
  /// In en, this message translates to:
  /// **'First person\'s birth city'**
  String get ashBirthCity1;

  /// No description provided for @ashBirthCity2.
  ///
  /// In en, this message translates to:
  /// **'Second person\'s birth city'**
  String get ashBirthCity2;

  /// No description provided for @ashCityHint.
  ///
  /// In en, this message translates to:
  /// **'City, country — e.g. Istanbul, Germany'**
  String get ashCityHint;

  /// No description provided for @ashManualOffset.
  ///
  /// In en, this message translates to:
  /// **'Enter UTC offset manually if the city is not found'**
  String get ashManualOffset;

  /// No description provided for @ashManualOffsetHint.
  ///
  /// In en, this message translates to:
  /// **'Rarely needed — the city is enough. For example Turkey +3, USA −5, India +5.5. Historical daylight saving (Turkey, USA, EU) is calculated automatically.'**
  String get ashManualOffsetHint;

  /// No description provided for @ashManualOffset1.
  ///
  /// In en, this message translates to:
  /// **'Person 1 UTC'**
  String get ashManualOffset1;

  /// No description provided for @ashManualOffset2.
  ///
  /// In en, this message translates to:
  /// **'Person 2 UTC'**
  String get ashManualOffset2;

  /// No description provided for @ashCityRequired1.
  ///
  /// In en, this message translates to:
  /// **'A birth city is required for the first person.'**
  String get ashCityRequired1;

  /// No description provided for @ashCityRequired2.
  ///
  /// In en, this message translates to:
  /// **'A birth city is required for the second person.'**
  String get ashCityRequired2;

  /// No description provided for @ashOffsetRange.
  ///
  /// In en, this message translates to:
  /// **'UTC offset must be between −12 and +14.'**
  String get ashOffsetRange;

  /// No description provided for @ashOverallReading.
  ///
  /// In en, this message translates to:
  /// **'Overall Reading'**
  String get ashOverallReading;

  /// No description provided for @ashResolvedUtc.
  ///
  /// In en, this message translates to:
  /// **'Birth location and time zone used'**
  String get ashResolvedUtc;

  /// No description provided for @ashOffsetApprox.
  ///
  /// In en, this message translates to:
  /// **'estimated'**
  String get ashOffsetApprox;

  /// No description provided for @ashOffsetManual.
  ///
  /// In en, this message translates to:
  /// **'entered manually'**
  String get ashOffsetManual;

  /// No description provided for @ashTimeAmbiguous.
  ///
  /// In en, this message translates to:
  /// **'DST transition hour'**
  String get ashTimeAmbiguous;

  /// No description provided for @ashCityNotInList.
  ///
  /// In en, this message translates to:
  /// **'This country has no city list. Use the manual UTC offset section below.'**
  String get ashCityNotInList;

  /// No description provided for @ashShowDetail.
  ///
  /// In en, this message translates to:
  /// **'Show technical detail'**
  String get ashShowDetail;

  /// No description provided for @ashHideDetail.
  ///
  /// In en, this message translates to:
  /// **'Hide technical detail'**
  String get ashHideDetail;

  /// No description provided for @analyzerFeaturesPy4.
  ///
  /// In en, this message translates to:
  /// **'Moon–Sun aspects, aspect map & celestial contract'**
  String get analyzerFeaturesPy4;

  /// No description provided for @analyzerFeaturesPy5.
  ///
  /// In en, this message translates to:
  /// **'Sabian degrees and life-area breakdown'**
  String get analyzerFeaturesPy5;

  /// No description provided for @analyzerFeaturesPy6.
  ///
  /// In en, this message translates to:
  /// **'Solar and lunar returns, yearly progression flow'**
  String get analyzerFeaturesPy6;

  /// No description provided for @analyzerFeaturesPy7.
  ///
  /// In en, this message translates to:
  /// **'Time machine: scan the sky of any year you choose'**
  String get analyzerFeaturesPy7;

  /// No description provided for @analyzerFeaturesPy8.
  ///
  /// In en, this message translates to:
  /// **'Arabic points radar and celestial seal analysis'**
  String get analyzerFeaturesPy8;

  /// No description provided for @analyzerFeaturesPy9.
  ///
  /// In en, this message translates to:
  /// **'Healing prescriptions and asteroid interactions'**
  String get analyzerFeaturesPy9;

  /// No description provided for @analyzerFeaturesPy10.
  ///
  /// In en, this message translates to:
  /// **'Astrocartography, chart drawings & graph screens'**
  String get analyzerFeaturesPy10;

  /// No description provided for @analyzerFeaturesPy11.
  ///
  /// In en, this message translates to:
  /// **'Full PDF report (unlimited download right)'**
  String get analyzerFeaturesPy11;

  /// No description provided for @analyzerFeaturesAsh1.
  ///
  /// In en, this message translates to:
  /// **'36-point compatibility score between moon nakshatras'**
  String get analyzerFeaturesAsh1;

  /// No description provided for @analyzerFeaturesAsh2.
  ///
  /// In en, this message translates to:
  /// **'Plain-language reading for each of the 8 areas, score by score'**
  String get analyzerFeaturesAsh2;

  /// No description provided for @analyzerFeaturesAsh3.
  ///
  /// In en, this message translates to:
  /// **'Moon profiles: lord, sign and direction details'**
  String get analyzerFeaturesAsh3;

  /// No description provided for @analyzerFeaturesAsh4.
  ///
  /// In en, this message translates to:
  /// **'Birth-place picker with historical time and DST correction'**
  String get analyzerFeaturesAsh4;

  /// No description provided for @analyzerFeaturesAsh5.
  ///
  /// In en, this message translates to:
  /// **'Detailed detection of inner friction (Nadi)'**
  String get analyzerFeaturesAsh5;

  /// No description provided for @analyzerFeaturesAsh6.
  ///
  /// In en, this message translates to:
  /// **'Warning and best-time suggestion when birth time is uncertain'**
  String get analyzerFeaturesAsh6;

  /// No description provided for @analyzerFeaturesAsh7.
  ///
  /// In en, this message translates to:
  /// **'Out-of-scope rules and transparent calculation notes'**
  String get analyzerFeaturesAsh7;

  /// No description provided for @analyzerFeaturesAsh8.
  ///
  /// In en, this message translates to:
  /// **'Full reading in TR / EN / ES'**
  String get analyzerFeaturesAsh8;

  /// No description provided for @analyzerFeaturesAsh9.
  ///
  /// In en, this message translates to:
  /// **'Full PDF report (unlimited download right)'**
  String get analyzerFeaturesAsh9;

  /// No description provided for @navHome.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get navHome;

  /// No description provided for @navCommunity.
  ///
  /// In en, this message translates to:
  /// **'Community'**
  String get navCommunity;

  /// No description provided for @navProfile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get navProfile;

  /// No description provided for @communityLoginTitle.
  ///
  /// In en, this message translates to:
  /// **'Join the astrology community'**
  String get communityLoginTitle;

  /// No description provided for @communityLoginSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Sign in to see posts, share your charts and follow other members. Synastry stays available to everyone.'**
  String get communityLoginSubtitle;

  /// No description provided for @communityLoginButton.
  ///
  /// In en, this message translates to:
  /// **'Sign in to join'**
  String get communityLoginButton;

  /// No description provided for @handleTitle.
  ///
  /// In en, this message translates to:
  /// **'Claim your @handle'**
  String get handleTitle;

  /// No description provided for @handleSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Pick a unique username. This is how others find and follow you.'**
  String get handleSubtitle;

  /// No description provided for @handleLabel.
  ///
  /// In en, this message translates to:
  /// **'Username'**
  String get handleLabel;

  /// No description provided for @handleDisplayName.
  ///
  /// In en, this message translates to:
  /// **'Display name'**
  String get handleDisplayName;

  /// No description provided for @handleDisplayNameHint.
  ///
  /// In en, this message translates to:
  /// **'How your name appears'**
  String get handleDisplayNameHint;

  /// No description provided for @handleBio.
  ///
  /// In en, this message translates to:
  /// **'Bio'**
  String get handleBio;

  /// No description provided for @handleBioHint.
  ///
  /// In en, this message translates to:
  /// **'A short line about you'**
  String get handleBioHint;

  /// No description provided for @handleBirthDate.
  ///
  /// In en, this message translates to:
  /// **'Birth date (optional)'**
  String get handleBirthDate;

  /// No description provided for @handleBirthDateHint.
  ///
  /// In en, this message translates to:
  /// **'Add your birth date to show your sun sign'**
  String get handleBirthDateHint;

  /// No description provided for @handleBirthPrivateNote.
  ///
  /// In en, this message translates to:
  /// **'Your birth date stays private. Only your sun sign badge is shown on your profile.'**
  String get handleBirthPrivateNote;

  /// No description provided for @kunyeBirthTime.
  ///
  /// In en, this message translates to:
  /// **'Birth time (optional)'**
  String get kunyeBirthTime;

  /// No description provided for @kunyeBirthTimeHint.
  ///
  /// In en, this message translates to:
  /// **'Pick a time'**
  String get kunyeBirthTimeHint;

  /// No description provided for @kunyeBirthTimeNote.
  ///
  /// In en, this message translates to:
  /// **'Adding your time pins your Sun and Moon sign degrees.'**
  String get kunyeBirthTimeNote;

  /// No description provided for @kunyeBirthCity.
  ///
  /// In en, this message translates to:
  /// **'Birth city (optional)'**
  String get kunyeBirthCity;

  /// No description provided for @kunyeBirthCityHint.
  ///
  /// In en, this message translates to:
  /// **'e.g. Istanbul'**
  String get kunyeBirthCityHint;

  /// No description provided for @kunyeCityNotFound.
  ///
  /// In en, this message translates to:
  /// **'City not found, check the name.'**
  String get kunyeCityNotFound;

  /// No description provided for @kunyeCalcNote.
  ///
  /// In en, this message translates to:
  /// **'Your Sun and Moon signs are calculated precisely on the server.'**
  String get kunyeCalcNote;

  /// No description provided for @kunyeRoleLabel.
  ///
  /// In en, this message translates to:
  /// **'Your relation to astrology'**
  String get kunyeRoleLabel;

  /// No description provided for @kunyeRoleAstrolog.
  ///
  /// In en, this message translates to:
  /// **'Astrologer'**
  String get kunyeRoleAstrolog;

  /// No description provided for @kunyeRoleLover.
  ///
  /// In en, this message translates to:
  /// **'Astrology enthusiast'**
  String get kunyeRoleLover;

  /// No description provided for @kunyeFieldLabel.
  ///
  /// In en, this message translates to:
  /// **'Your field'**
  String get kunyeFieldLabel;

  /// No description provided for @settingsTitle.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settingsTitle;

  /// No description provided for @settingsAppearance.
  ///
  /// In en, this message translates to:
  /// **'Appearance'**
  String get settingsAppearance;

  /// No description provided for @settingsLanguage.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get settingsLanguage;

  /// No description provided for @settingsNotifications.
  ///
  /// In en, this message translates to:
  /// **'Notifications'**
  String get settingsNotifications;

  /// No description provided for @settingsDailyReminder.
  ///
  /// In en, this message translates to:
  /// **'Daily reminder (09:00)'**
  String get settingsDailyReminder;

  /// No description provided for @settingsSubscription.
  ///
  /// In en, this message translates to:
  /// **'Subscription'**
  String get settingsSubscription;

  /// No description provided for @settingsProActive.
  ///
  /// In en, this message translates to:
  /// **'Pro active'**
  String get settingsProActive;

  /// No description provided for @settingsProFree.
  ///
  /// In en, this message translates to:
  /// **'Free plan'**
  String get settingsProFree;

  /// No description provided for @settingsManagePro.
  ///
  /// In en, this message translates to:
  /// **'Manage Pro'**
  String get settingsManagePro;

  /// No description provided for @settingsRestore.
  ///
  /// In en, this message translates to:
  /// **'Restore purchases'**
  String get settingsRestore;

  /// No description provided for @settingsAccount.
  ///
  /// In en, this message translates to:
  /// **'Account'**
  String get settingsAccount;

  /// No description provided for @settingsAbout.
  ///
  /// In en, this message translates to:
  /// **'About'**
  String get settingsAbout;

  /// No description provided for @settingsVersion.
  ///
  /// In en, this message translates to:
  /// **'Version'**
  String get settingsVersion;

  /// No description provided for @settingsSignOut.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get settingsSignOut;

  /// No description provided for @profileShare.
  ///
  /// In en, this message translates to:
  /// **'Share profile'**
  String get profileShare;

  /// No description provided for @postShareSend.
  ///
  /// In en, this message translates to:
  /// **'Send'**
  String get postShareSend;

  /// No description provided for @postShareStory.
  ///
  /// In en, this message translates to:
  /// **'Add to my story'**
  String get postShareStory;

  /// No description provided for @postShareSystem.
  ///
  /// In en, this message translates to:
  /// **'Share'**
  String get postShareSystem;

  /// No description provided for @postShareTitle.
  ///
  /// In en, this message translates to:
  /// **'Share post'**
  String get postShareTitle;

  /// No description provided for @shareToTitle.
  ///
  /// In en, this message translates to:
  /// **'Send to…'**
  String get shareToTitle;

  /// No description provided for @shareNoFollowing.
  ///
  /// In en, this message translates to:
  /// **'You are not following anyone yet.'**
  String get shareNoFollowing;

  /// No description provided for @shareSent.
  ///
  /// In en, this message translates to:
  /// **'Sent'**
  String get shareSent;

  /// No description provided for @shareFailed.
  ///
  /// In en, this message translates to:
  /// **'Could not share'**
  String get shareFailed;

  /// No description provided for @storyRepostAdded.
  ///
  /// In en, this message translates to:
  /// **'Added to your story'**
  String get storyRepostAdded;

  /// No description provided for @storyRepostFailed.
  ///
  /// In en, this message translates to:
  /// **'Could not add to story'**
  String get storyRepostFailed;

  /// No description provided for @shareProfileMessage.
  ///
  /// In en, this message translates to:
  /// **'@{handle} — Holavon astrology community'**
  String shareProfileMessage(String handle);

  /// No description provided for @feedFollowingTab.
  ///
  /// In en, this message translates to:
  /// **'Following'**
  String get feedFollowingTab;

  /// No description provided for @feedDiscoverTab.
  ///
  /// In en, this message translates to:
  /// **'Discover'**
  String get feedDiscoverTab;

  /// No description provided for @feedFollowingEmpty.
  ///
  /// In en, this message translates to:
  /// **'Posts from people you follow will appear here.'**
  String get feedFollowingEmpty;

  /// No description provided for @feedDiscoverCta.
  ///
  /// In en, this message translates to:
  /// **'Go to Discover'**
  String get feedDiscoverCta;

  /// No description provided for @skyTitle.
  ///
  /// In en, this message translates to:
  /// **'Sky'**
  String get skyTitle;

  /// No description provided for @skyMoonLine.
  ///
  /// In en, this message translates to:
  /// **'Moon {sign} {degree}°'**
  String skyMoonLine(String sign, String degree);

  /// No description provided for @skyIllumination.
  ///
  /// In en, this message translates to:
  /// **'%{pct} illuminated'**
  String skyIllumination(String pct);

  /// No description provided for @skySpeedSlow.
  ///
  /// In en, this message translates to:
  /// **'slow'**
  String get skySpeedSlow;

  /// No description provided for @skySpeedNormal.
  ///
  /// In en, this message translates to:
  /// **'normal'**
  String get skySpeedNormal;

  /// No description provided for @skySpeedFast.
  ///
  /// In en, this message translates to:
  /// **'fast'**
  String get skySpeedFast;

  /// No description provided for @skyVoid.
  ///
  /// In en, this message translates to:
  /// **'Moon void of course'**
  String get skyVoid;

  /// No description provided for @skyNotVoid.
  ///
  /// In en, this message translates to:
  /// **'Moon in flow'**
  String get skyNotVoid;

  /// No description provided for @skyVoidUntil.
  ///
  /// In en, this message translates to:
  /// **'Void until {time}'**
  String skyVoidUntil(String time);

  /// No description provided for @skyPlanetHour.
  ///
  /// In en, this message translates to:
  /// **'{planet} hour'**
  String skyPlanetHour(String planet);

  /// No description provided for @skyNextHour.
  ///
  /// In en, this message translates to:
  /// **'Next: {planet} hour'**
  String skyNextHour(String planet);

  /// No description provided for @skyAspects.
  ///
  /// In en, this message translates to:
  /// **'Moon aspects'**
  String get skyAspects;

  /// No description provided for @skyNoAspects.
  ///
  /// In en, this message translates to:
  /// **'No major aspect right now'**
  String get skyNoAspects;

  /// No description provided for @skyRetro.
  ///
  /// In en, this message translates to:
  /// **'Retrograde'**
  String get skyRetro;

  /// No description provided for @skySunLine.
  ///
  /// In en, this message translates to:
  /// **'Sun {sign} {degree}°'**
  String skySunLine(String sign, String degree);

  /// No description provided for @skyPhaseNew.
  ///
  /// In en, this message translates to:
  /// **'New Moon'**
  String get skyPhaseNew;

  /// No description provided for @skyPhaseWaxingCrescent.
  ///
  /// In en, this message translates to:
  /// **'Waxing Crescent'**
  String get skyPhaseWaxingCrescent;

  /// No description provided for @skyPhaseFirstQuarter.
  ///
  /// In en, this message translates to:
  /// **'First Quarter'**
  String get skyPhaseFirstQuarter;

  /// No description provided for @skyPhaseWaxingGibbous.
  ///
  /// In en, this message translates to:
  /// **'Waxing Gibbous'**
  String get skyPhaseWaxingGibbous;

  /// No description provided for @skyPhaseFull.
  ///
  /// In en, this message translates to:
  /// **'Full Moon'**
  String get skyPhaseFull;

  /// No description provided for @skyPhaseWaningGibbous.
  ///
  /// In en, this message translates to:
  /// **'Waning Gibbous'**
  String get skyPhaseWaningGibbous;

  /// No description provided for @skyPhaseLastQuarter.
  ///
  /// In en, this message translates to:
  /// **'Last Quarter'**
  String get skyPhaseLastQuarter;

  /// No description provided for @skyPhaseWaningCrescent.
  ///
  /// In en, this message translates to:
  /// **'Waning Crescent'**
  String get skyPhaseWaningCrescent;

  /// No description provided for @skyDayHour.
  ///
  /// In en, this message translates to:
  /// **'day hour'**
  String get skyDayHour;

  /// No description provided for @skyNightHour.
  ///
  /// In en, this message translates to:
  /// **'night hour'**
  String get skyNightHour;

  /// No description provided for @skyCalendarTitle.
  ///
  /// In en, this message translates to:
  /// **'Sky Calendar'**
  String get skyCalendarTitle;

  /// No description provided for @skyCalendarPhases.
  ///
  /// In en, this message translates to:
  /// **'Moon Phases'**
  String get skyCalendarPhases;

  /// No description provided for @skyCalendarEclipses.
  ///
  /// In en, this message translates to:
  /// **'Eclipses'**
  String get skyCalendarEclipses;

  /// No description provided for @skyCalendarOpen.
  ///
  /// In en, this message translates to:
  /// **'Open calendar'**
  String get skyCalendarOpen;

  /// No description provided for @skyCalendarEmpty.
  ///
  /// In en, this message translates to:
  /// **'No upcoming events'**
  String get skyCalendarEmpty;

  /// No description provided for @skyCalendarNow.
  ///
  /// In en, this message translates to:
  /// **'now'**
  String get skyCalendarNow;

  /// No description provided for @skyCalendarToday.
  ///
  /// In en, this message translates to:
  /// **'today'**
  String get skyCalendarToday;

  /// No description provided for @skyCalendarTomorrow.
  ///
  /// In en, this message translates to:
  /// **'tomorrow'**
  String get skyCalendarTomorrow;

  /// No description provided for @skyCalendarInDays.
  ///
  /// In en, this message translates to:
  /// **'in {days} days'**
  String skyCalendarInDays(String days);

  /// No description provided for @skyCalendarInHours.
  ///
  /// In en, this message translates to:
  /// **'in {hours} h'**
  String skyCalendarInHours(String hours);

  /// No description provided for @skyNewMoon.
  ///
  /// In en, this message translates to:
  /// **'New Moon'**
  String get skyNewMoon;

  /// No description provided for @skyFullMoon.
  ///
  /// In en, this message translates to:
  /// **'Full Moon'**
  String get skyFullMoon;

  /// No description provided for @skyEclipseSolar.
  ///
  /// In en, this message translates to:
  /// **'Solar eclipse'**
  String get skyEclipseSolar;

  /// No description provided for @skyEclipseLunar.
  ///
  /// In en, this message translates to:
  /// **'Lunar eclipse'**
  String get skyEclipseLunar;

  /// No description provided for @skyEclipseTotal.
  ///
  /// In en, this message translates to:
  /// **'total'**
  String get skyEclipseTotal;

  /// No description provided for @skyEclipseAnnular.
  ///
  /// In en, this message translates to:
  /// **'annular'**
  String get skyEclipseAnnular;

  /// No description provided for @skyEclipsePartial.
  ///
  /// In en, this message translates to:
  /// **'partial'**
  String get skyEclipsePartial;

  /// No description provided for @skyEclipseHybrid.
  ///
  /// In en, this message translates to:
  /// **'hybrid'**
  String get skyEclipseHybrid;

  /// No description provided for @skyEclipsePenumbral.
  ///
  /// In en, this message translates to:
  /// **'penumbral'**
  String get skyEclipsePenumbral;

  /// No description provided for @skyEclipseVisibleHere.
  ///
  /// In en, this message translates to:
  /// **'visible from here'**
  String get skyEclipseVisibleHere;

  /// No description provided for @skyEclipseNotVisible.
  ///
  /// In en, this message translates to:
  /// **'not visible here'**
  String get skyEclipseNotVisible;

  /// No description provided for @skyEclipseNextVisible.
  ///
  /// In en, this message translates to:
  /// **'Next visible: {when}'**
  String skyEclipseNextVisible(String when);

  /// No description provided for @skyEclipseObscuration.
  ///
  /// In en, this message translates to:
  /// **'{pct}% covered'**
  String skyEclipseObscuration(String pct);

  /// No description provided for @skyPerDay.
  ///
  /// In en, this message translates to:
  /// **'{value}°/day'**
  String skyPerDay(String value);

  /// No description provided for @skyMoonSpeed.
  ///
  /// In en, this message translates to:
  /// **'Moon speed'**
  String get skyMoonSpeed;

  /// No description provided for @handleTooShort.
  ///
  /// In en, this message translates to:
  /// **'Username must be at least 3 characters.'**
  String get handleTooShort;

  /// No description provided for @handleInvalid.
  ///
  /// In en, this message translates to:
  /// **'Only lowercase letters, numbers, dots and underscores.'**
  String get handleInvalid;

  /// No description provided for @handleTaken.
  ///
  /// In en, this message translates to:
  /// **'That username is already taken.'**
  String get handleTaken;

  /// No description provided for @handleContinue.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get handleContinue;

  /// No description provided for @postReport.
  ///
  /// In en, this message translates to:
  /// **'Report'**
  String get postReport;

  /// No description provided for @blockUser.
  ///
  /// In en, this message translates to:
  /// **'Block user'**
  String get blockUser;

  /// No description provided for @postDelete.
  ///
  /// In en, this message translates to:
  /// **'Delete post'**
  String get postDelete;

  /// No description provided for @reportSent.
  ///
  /// In en, this message translates to:
  /// **'Report sent. Thank you.'**
  String get reportSent;

  /// No description provided for @blockDone.
  ///
  /// In en, this message translates to:
  /// **'User blocked.'**
  String get blockDone;

  /// No description provided for @timeJustNow.
  ///
  /// In en, this message translates to:
  /// **'just now'**
  String get timeJustNow;

  /// timeMinutes
  ///
  /// In en, this message translates to:
  /// **'{n}m'**
  String timeMinutes(int n);

  /// timeHours
  ///
  /// In en, this message translates to:
  /// **'{n}h'**
  String timeHours(int n);

  /// timeDays
  ///
  /// In en, this message translates to:
  /// **'{n}d'**
  String timeDays(int n);

  /// No description provided for @feedEmpty.
  ///
  /// In en, this message translates to:
  /// **'No posts yet'**
  String get feedEmpty;

  /// No description provided for @feedEmptyHint.
  ///
  /// In en, this message translates to:
  /// **'Be the first to share something astrological.'**
  String get feedEmptyHint;

  /// No description provided for @createPostTitle.
  ///
  /// In en, this message translates to:
  /// **'New post'**
  String get createPostTitle;

  /// No description provided for @createPostShare.
  ///
  /// In en, this message translates to:
  /// **'Share'**
  String get createPostShare;

  /// No description provided for @createPostNoImage.
  ///
  /// In en, this message translates to:
  /// **'Choose an image first.'**
  String get createPostNoImage;

  /// No description provided for @createPostError.
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Try again.'**
  String get createPostError;

  /// No description provided for @createPostPick.
  ///
  /// In en, this message translates to:
  /// **'Tap to choose a photo'**
  String get createPostPick;

  /// No description provided for @createPostGallery.
  ///
  /// In en, this message translates to:
  /// **'Choose from gallery'**
  String get createPostGallery;

  /// No description provided for @mediaSourceTitle.
  ///
  /// In en, this message translates to:
  /// **'Photo source'**
  String get mediaSourceTitle;

  /// No description provided for @mediaCamera.
  ///
  /// In en, this message translates to:
  /// **'Camera'**
  String get mediaCamera;

  /// No description provided for @mediaGallery.
  ///
  /// In en, this message translates to:
  /// **'Gallery'**
  String get mediaGallery;

  /// No description provided for @mediaChange.
  ///
  /// In en, this message translates to:
  /// **'Change photo'**
  String get mediaChange;

  /// No description provided for @mediaCameraDenied.
  ///
  /// In en, this message translates to:
  /// **'Camera permission denied. Allow camera access for Holavon in your phone settings.'**
  String get mediaCameraDenied;

  /// No description provided for @mediaPickError.
  ///
  /// In en, this message translates to:
  /// **'Could not get the photo. Try again.'**
  String get mediaPickError;

  /// No description provided for @createPostChartBadge.
  ///
  /// In en, this message translates to:
  /// **'Chart'**
  String get createPostChartBadge;

  /// No description provided for @createPostCaptionHint.
  ///
  /// In en, this message translates to:
  /// **'Write a caption...'**
  String get createPostCaptionHint;

  /// No description provided for @profilePosts.
  ///
  /// In en, this message translates to:
  /// **'Posts'**
  String get profilePosts;

  /// No description provided for @profileFollowers.
  ///
  /// In en, this message translates to:
  /// **'Followers'**
  String get profileFollowers;

  /// No description provided for @profileFollowing.
  ///
  /// In en, this message translates to:
  /// **'Following'**
  String get profileFollowing;

  /// No description provided for @profilePlanets.
  ///
  /// In en, this message translates to:
  /// **'Natal chart'**
  String get profilePlanets;

  /// No description provided for @storyCreateTitle.
  ///
  /// In en, this message translates to:
  /// **'New story'**
  String get storyCreateTitle;

  /// No description provided for @storyMention.
  ///
  /// In en, this message translates to:
  /// **'Tag people'**
  String get storyMention;

  /// No description provided for @storyMentioned.
  ///
  /// In en, this message translates to:
  /// **'tagged'**
  String get storyMentioned;

  /// No description provided for @storyMine.
  ///
  /// In en, this message translates to:
  /// **'Your story'**
  String get storyMine;

  /// No description provided for @storyAdd.
  ///
  /// In en, this message translates to:
  /// **'Add story'**
  String get storyAdd;

  /// No description provided for @editImageHint.
  ///
  /// In en, this message translates to:
  /// **'Pinch to zoom · tap arrows to rotate'**
  String get editImageHint;

  /// No description provided for @profileEdit.
  ///
  /// In en, this message translates to:
  /// **'Edit profile'**
  String get profileEdit;

  /// No description provided for @profileFollow.
  ///
  /// In en, this message translates to:
  /// **'Follow'**
  String get profileFollow;

  /// No description provided for @profileFollowingBtn.
  ///
  /// In en, this message translates to:
  /// **'Following'**
  String get profileFollowingBtn;

  /// No description provided for @profileNoPosts.
  ///
  /// In en, this message translates to:
  /// **'No posts yet.'**
  String get profileNoPosts;

  /// No description provided for @profileNoPostsMe.
  ///
  /// In en, this message translates to:
  /// **'Share your first post from the + button.'**
  String get profileNoPostsMe;

  /// No description provided for @commentsTitle.
  ///
  /// In en, this message translates to:
  /// **'Comments'**
  String get commentsTitle;

  /// No description provided for @commentsEmpty.
  ///
  /// In en, this message translates to:
  /// **'No comments yet.'**
  String get commentsEmpty;

  /// No description provided for @commentsHint.
  ///
  /// In en, this message translates to:
  /// **'Add a comment...'**
  String get commentsHint;

  /// No description provided for @searchHint.
  ///
  /// In en, this message translates to:
  /// **'Search people'**
  String get searchHint;

  /// No description provided for @searchEmpty.
  ///
  /// In en, this message translates to:
  /// **'No users found.'**
  String get searchEmpty;

  /// No description provided for @searchPrompt.
  ///
  /// In en, this message translates to:
  /// **'Search for people to follow.'**
  String get searchPrompt;

  /// viewAllComments
  ///
  /// In en, this message translates to:
  /// **'View all {n} comments'**
  String viewAllComments(int n);

  /// No description provided for @createPostProcessing.
  ///
  /// In en, this message translates to:
  /// **'Preparing your chart...'**
  String get createPostProcessing;

  /// No description provided for @hubWelcome.
  ///
  /// In en, this message translates to:
  /// **'Welcome'**
  String get hubWelcome;

  /// No description provided for @hubChoose.
  ///
  /// In en, this message translates to:
  /// **'Where to?'**
  String get hubChoose;

  /// No description provided for @hubSocialTitle.
  ///
  /// In en, this message translates to:
  /// **'Holavon'**
  String get hubSocialTitle;

  /// No description provided for @hubSocialDesc.
  ///
  /// In en, this message translates to:
  /// **'Share, add stories, connect with the community'**
  String get hubSocialDesc;

  /// No description provided for @hubAnalysisTitle.
  ///
  /// In en, this message translates to:
  /// **'Fast Synastry'**
  String get hubAnalysisTitle;

  /// No description provided for @hubAnalysisDesc.
  ///
  /// In en, this message translates to:
  /// **'Synastry, natal and potential analyses'**
  String get hubAnalysisDesc;

  /// No description provided for @hubHoraryTitle.
  ///
  /// In en, this message translates to:
  /// **'Horary Oracle'**
  String get hubHoraryTitle;

  /// No description provided for @hubHoraryDesc.
  ///
  /// In en, this message translates to:
  /// **'A clear answer from the chart of the moment'**
  String get hubHoraryDesc;

  /// No description provided for @horaryTitle.
  ///
  /// In en, this message translates to:
  /// **'Horary Oracle'**
  String get horaryTitle;

  /// No description provided for @horarySubtitle.
  ///
  /// In en, this message translates to:
  /// **'Type your one question; I\'ll cast the chart of the moment.'**
  String get horarySubtitle;

  /// No description provided for @horaryQuestionHint.
  ///
  /// In en, this message translates to:
  /// **'Write your question... (e.g. will I get this job?)'**
  String get horaryQuestionHint;

  /// No description provided for @horaryAsk.
  ///
  /// In en, this message translates to:
  /// **'Ask ✨'**
  String get horaryAsk;

  /// No description provided for @horaryCategory.
  ///
  /// In en, this message translates to:
  /// **'Category'**
  String get horaryCategory;

  /// No description provided for @horaryAsker.
  ///
  /// In en, this message translates to:
  /// **'Whose rising?'**
  String get horaryAsker;

  /// No description provided for @horaryAskerMe.
  ///
  /// In en, this message translates to:
  /// **'Me'**
  String get horaryAskerMe;

  /// No description provided for @horaryAskerOther.
  ///
  /// In en, this message translates to:
  /// **'Someone else'**
  String get horaryAskerOther;

  /// No description provided for @horaryLocation.
  ///
  /// In en, this message translates to:
  /// **'Location'**
  String get horaryLocation;

  /// No description provided for @horaryLocationHint.
  ///
  /// In en, this message translates to:
  /// **'Choose your location before asking'**
  String get horaryLocationHint;

  /// No description provided for @horaryVerdict.
  ///
  /// In en, this message translates to:
  /// **'Verdict'**
  String get horaryVerdict;

  /// No description provided for @horaryTiming.
  ///
  /// In en, this message translates to:
  /// **'Timing'**
  String get horaryTiming;

  /// No description provided for @horaryDetailsShow.
  ///
  /// In en, this message translates to:
  /// **'Show details'**
  String get horaryDetailsShow;

  /// No description provided for @horaryDetailsHide.
  ///
  /// In en, this message translates to:
  /// **'Hide details'**
  String get horaryDetailsHide;

  /// No description provided for @horaryAsc.
  ///
  /// In en, this message translates to:
  /// **'Ascendant'**
  String get horaryAsc;

  /// No description provided for @editorRotateHint.
  ///
  /// In en, this message translates to:
  /// **'Hold & rotate'**
  String get editorRotateHint;

  /// No description provided for @dmTitle.
  ///
  /// In en, this message translates to:
  /// **'Chat'**
  String get dmTitle;

  /// No description provided for @dmInboxTitle.
  ///
  /// In en, this message translates to:
  /// **'Messages'**
  String get dmInboxTitle;

  /// No description provided for @dmInboxEmpty.
  ///
  /// In en, this message translates to:
  /// **'No messages yet. Tap \"Message\" on someone\'s profile to start a chat.'**
  String get dmInboxEmpty;

  /// No description provided for @dmMessage.
  ///
  /// In en, this message translates to:
  /// **'Message'**
  String get dmMessage;

  /// No description provided for @dmHint.
  ///
  /// In en, this message translates to:
  /// **'Type a message...'**
  String get dmHint;

  /// No description provided for @dmEmpty.
  ///
  /// In en, this message translates to:
  /// **'No messages yet. Send the first one.'**
  String get dmEmpty;

  /// No description provided for @dmSendError.
  ///
  /// In en, this message translates to:
  /// **'Message could not be sent.'**
  String get dmSendError;

  /// No description provided for @horaryMoon.
  ///
  /// In en, this message translates to:
  /// **'Moon'**
  String get horaryMoon;

  /// No description provided for @horaryNoCredits.
  ///
  /// In en, this message translates to:
  /// **'You\'re out of credits. Please get a credit pack.'**
  String get horaryNoCredits;

  /// No description provided for @horaryError.
  ///
  /// In en, this message translates to:
  /// **'Couldn\'t get an answer. Try again.'**
  String get horaryError;

  /// No description provided for @horaryCatGeneral.
  ///
  /// In en, this message translates to:
  /// **'Automatic'**
  String get horaryCatGeneral;

  /// No description provided for @horaryCatRelationship.
  ///
  /// In en, this message translates to:
  /// **'Relationship'**
  String get horaryCatRelationship;

  /// No description provided for @horaryCatMoney.
  ///
  /// In en, this message translates to:
  /// **'Money'**
  String get horaryCatMoney;

  /// No description provided for @horaryCatJob.
  ///
  /// In en, this message translates to:
  /// **'Job/Career'**
  String get horaryCatJob;

  /// No description provided for @horaryCatHealth.
  ///
  /// In en, this message translates to:
  /// **'Health'**
  String get horaryCatHealth;

  /// No description provided for @horaryCatLostObject.
  ///
  /// In en, this message translates to:
  /// **'Lost Object'**
  String get horaryCatLostObject;

  /// No description provided for @horaryCatMissingPerson.
  ///
  /// In en, this message translates to:
  /// **'Missing Person'**
  String get horaryCatMissingPerson;

  /// No description provided for @horaryCatHouse.
  ///
  /// In en, this message translates to:
  /// **'House/Property'**
  String get horaryCatHouse;

  /// No description provided for @horaryCatChild.
  ///
  /// In en, this message translates to:
  /// **'Child'**
  String get horaryCatChild;

  /// No description provided for @horaryCatPet.
  ///
  /// In en, this message translates to:
  /// **'Pet'**
  String get horaryCatPet;

  /// No description provided for @horarySuggestLabel.
  ///
  /// In en, this message translates to:
  /// **'Example questions'**
  String get horarySuggestLabel;

  /// No description provided for @horarySuggestRelationship.
  ///
  /// In en, this message translates to:
  /// **'Does he love me? | Will we reconcile? | Will we marry?'**
  String get horarySuggestRelationship;

  /// No description provided for @horarySuggestJob.
  ///
  /// In en, this message translates to:
  /// **'Will I get this job? | Will I get promoted? | Will this work out?'**
  String get horarySuggestJob;

  /// No description provided for @horarySuggestMoney.
  ///
  /// In en, this message translates to:
  /// **'Will money come? | Will the debt be paid? | Will I buy a house?'**
  String get horarySuggestMoney;

  /// No description provided for @horarySuggestLostObject.
  ///
  /// In en, this message translates to:
  /// **'Where is it? | Will I find it? | Who took it?'**
  String get horarySuggestLostObject;

  /// No description provided for @horarySuggestHealth.
  ///
  /// In en, this message translates to:
  /// **'Will I recover? | Should I have surgery?'**
  String get horarySuggestHealth;

  /// No description provided for @horarySuggestDefault.
  ///
  /// In en, this message translates to:
  /// **'Will I get this job? | Will they text me? | Will I have a home?'**
  String get horarySuggestDefault;

  /// No description provided for @horaryIntroTitle.
  ///
  /// In en, this message translates to:
  /// **'Asking the Right Question in Horary'**
  String get horaryIntroTitle;

  /// No description provided for @horaryIntroSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Not fortune-telling, the language of the moment'**
  String get horaryIntroSubtitle;

  /// No description provided for @horaryIntroR1.
  ///
  /// In en, this message translates to:
  /// **'Ask when you truly need to — not out of curiosity, but when your heart is heavy. Don\'t repeat the same question every 2-3 days.'**
  String get horaryIntroR1;

  /// No description provided for @horaryIntroR2.
  ///
  /// In en, this message translates to:
  /// **'Ask one clear question — a single sentence like “Will I get this job?”'**
  String get horaryIntroR2;

  /// No description provided for @horaryIntroR3.
  ///
  /// In en, this message translates to:
  /// **'Expect radicality — if the chart is at 0-1°/29° or the Moon is void, it says “not flowing now”; ask again in 1-2 days.'**
  String get horaryIntroR3;

  /// No description provided for @horaryIntroR4.
  ///
  /// In en, this message translates to:
  /// **'Give honest time and place — the moment the question came to you, and your city.'**
  String get horaryIntroR4;

  /// No description provided for @horaryIntroR5.
  ///
  /// In en, this message translates to:
  /// **'Listen to the answer as it is — “hard but it will happen” is also an answer; Saturn\'s delay is part of it.'**
  String get horaryIntroR5;

  /// No description provided for @horaryIntroFooter.
  ///
  /// In en, this message translates to:
  /// **'When ready, ask — the sky is listening. ✨'**
  String get horaryIntroFooter;

  /// No description provided for @horaryIntroDontShow.
  ///
  /// In en, this message translates to:
  /// **'Don\'t show again'**
  String get horaryIntroDontShow;

  /// No description provided for @horaryIntroOk.
  ///
  /// In en, this message translates to:
  /// **'Got it, Ask the Question ✨'**
  String get horaryIntroOk;

  /// No description provided for @proEntry.
  ///
  /// In en, this message translates to:
  /// **'Go Pro'**
  String get proEntry;

  /// No description provided for @proPaywallTitle.
  ///
  /// In en, this message translates to:
  /// **'Holavon Pro'**
  String get proPaywallTitle;

  /// No description provided for @proBenefitHorary.
  ///
  /// In en, this message translates to:
  /// **'Pro: unlimited horary questions'**
  String get proBenefitHorary;

  /// No description provided for @proBenefitAnalysis.
  ///
  /// In en, this message translates to:
  /// **'Pro: unlimited PDF reports'**
  String get proBenefitAnalysis;

  /// No description provided for @horaryQuota.
  ///
  /// In en, this message translates to:
  /// **'Questions left today:'**
  String get horaryQuota;

  /// No description provided for @horaryLimitTitle.
  ///
  /// In en, this message translates to:
  /// **'Free Daily Questions Used Up'**
  String get horaryLimitTitle;

  /// No description provided for @horaryLimitDesc.
  ///
  /// In en, this message translates to:
  /// **'On the free plan you can ask 3 questions per day. Pro unlocks unlimited questions and all PDF reports.'**
  String get horaryLimitDesc;

  /// No description provided for @horaryLimitLater.
  ///
  /// In en, this message translates to:
  /// **'Come back tomorrow'**
  String get horaryLimitLater;

  /// No description provided for @horaryAuthError.
  ///
  /// In en, this message translates to:
  /// **'Session could not be verified. Please sign in again and retry.'**
  String get horaryAuthError;

  /// No description provided for @horaryCredits.
  ///
  /// In en, this message translates to:
  /// **'credits'**
  String get horaryCredits;

  /// No description provided for @horaryClear.
  ///
  /// In en, this message translates to:
  /// **'Clear chat'**
  String get horaryClear;

  /// No description provided for @horaryCopy.
  ///
  /// In en, this message translates to:
  /// **'Copy'**
  String get horaryCopy;

  /// No description provided for @horaryLocationWarning.
  ///
  /// In en, this message translates to:
  /// **'Set your location before asking the question.'**
  String get horaryLocationWarning;

  /// No description provided for @horaryNoticeBody.
  ///
  /// In en, this message translates to:
  /// **'Horary is not fortune-telling; it is the language of the moment. The sky answers; the chart of the question\'s moment is cast. Ask one clear question when you truly need an answer. Wait for radicality — if the chart is on a boundary or the Moon is void, it says \"not flowing now\"; ask again in 1-2 days.'**
  String get horaryNoticeBody;

  /// No description provided for @noticeDontShow.
  ///
  /// In en, this message translates to:
  /// **'Don\'t show again'**
  String get noticeDontShow;

  /// No description provided for @proPillarAnalysis.
  ///
  /// In en, this message translates to:
  /// **'Fast Synastry'**
  String get proPillarAnalysis;

  /// No description provided for @proPillarAnalysisDesc.
  ///
  /// In en, this message translates to:
  /// **'Unlimited full PDF report downloads across all modes.'**
  String get proPillarAnalysisDesc;

  /// No description provided for @proPillarHorary.
  ///
  /// In en, this message translates to:
  /// **'Horary Oracle'**
  String get proPillarHorary;

  /// No description provided for @proPillarHoraryDesc.
  ///
  /// In en, this message translates to:
  /// **'The 3-questions-a-day limit is lifted; unlimited horary questions.'**
  String get proPillarHoraryDesc;

  /// No description provided for @proPillarSocial.
  ///
  /// In en, this message translates to:
  /// **'Social'**
  String get proPillarSocial;

  /// No description provided for @proPillarSocialDesc.
  ///
  /// In en, this message translates to:
  /// **'The community is free and unlimited for everyone — share, add stories, interact.'**
  String get proPillarSocialDesc;
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
      <String>['en', 'es', 'tr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
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
