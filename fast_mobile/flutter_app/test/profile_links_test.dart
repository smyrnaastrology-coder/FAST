import 'package:fast_app/services/profile_links.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const id = '05b5479c-3147-4200-9340-1fdbe7a2f17f';

  test('shared profile URL targets the public landing page', () {
    expect(ProfileLinks.publicUrl(id), 'https://fbst-api-mzum.onrender.com/u/$id');
    expect(ProfileLinks.publicUrl('not-a-uuid'), isNull);
  });

  test('only valid profile app links are accepted', () {
    expect(ProfileLinks.userIdFromUri(Uri.parse('com.fastastrology.fast://profile/$id')), id);
    for (final bad in [
      'com.fastastrology.fast://login-callback/$id',
      'https://fbst-api-mzum.onrender.com/u/$id',
      'com.fastastrology.fast://profile/not-a-uuid',
      'com.fastastrology.fast://profile/$id/extra',
      'com.fastastrology.fast://profile/$id?other=1',
    ]) {
      expect(ProfileLinks.userIdFromUri(Uri.parse(bad)), isNull);
    }
  });
}
