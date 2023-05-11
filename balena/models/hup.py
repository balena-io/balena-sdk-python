import semver

from .. import exceptions


class Hup:
    """ """

    MIN_TARGET_VERSION = "2.2.0+rev1"

    def get_hup_action_type(self, device_type, current_version, target_version):
        """
        getHUPActionType in Python
        ref: https://github.com/balena-io-modules/balena-hup-action-utils/blob/master/lib/index.ts#L67
        """

        try:
            parsed_current_ver = semver.parse(current_version)
        except Exception:
            raise exceptions.OsUpdateError("Invalid current balenaOS version")

        try:
            parsed_target_ver = semver.parse(target_version)
        except Exception:
            raise exceptions.OsUpdateError("Invalid target balenaOS version")

        if parsed_current_ver["prerelease"] or parsed_target_ver["prerelease"]:
            raise exceptions.OsUpdateError("Updates cannot be performed on pre-release balenaOS versions")

        cur_variant = self.__get_variant(parsed_current_ver)
        target_variant = self.__get_variant(parsed_target_ver)

        if target_variant is not None and ((cur_variant == "dev") != (target_variant == "dev")):
            raise exceptions.OsUpdateError(
                "Updates cannot be performed between development and production balenaOS variants"
            )

        if semver.compare(target_version, current_version) < 0:
            raise exceptions.OsUpdateError("OS downgrades are not allowed")

        # For 1.x -> 2.x or 2.x to 2.x only
        if parsed_target_ver["major"] > 1 and semver.compare(target_version, self.MIN_TARGET_VERSION) < 0:
            raise exceptions.OsUpdateError(
                "Target balenaOS version must be greater than {0}".format(self.MIN_TARGET_VERSION)
            )

        return "resinhup{from_v}{to_v}".format(from_v=parsed_current_ver["major"], to_v=parsed_target_ver["major"])

    def __get_variant(self, ver):
        if "dev" in (ver["build"] or "") or "dev" in (ver["prerelease"] or ""):
            return "dev"
        if "prod" in (ver["build"] or "") or "prod" in (ver["prerelease"] or ""):
            return "prod"
        return None
