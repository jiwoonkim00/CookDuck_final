package com.api.dto;

import com.google.gson.annotations.SerializedName;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class KakaoUserInfoResponse {
    private Long id;

    @SerializedName("connected_at")
    private String connectedAt;

    private Properties properties;

    @SerializedName("kakao_account")
    private KakaoAccount kakaoAccount;

    @Getter
    @Setter
    public static class Properties {
        private String nickname;
        
        @SerializedName("profile_image")
        private String profileImage;
        
        @SerializedName("thumbnail_image")
        private String thumbnailImage;
    }

    @Getter
    @Setter
    public static class KakaoAccount {
        @SerializedName("profile_nickname_needs_agreement")
        private Boolean profileNicknameNeedsAgreement;

        @SerializedName("profile_image_needs_agreement")
        private Boolean profileImageNeedsAgreement;

        private Profile profile;

        @SerializedName("has_email")
        private Boolean hasEmail;

        @SerializedName("email_needs_agreement")
        private Boolean emailNeedsAgreement;

        @SerializedName("is_email_valid")
        private Boolean isEmailValid;

        @SerializedName("is_email_verified")
        private Boolean isEmailVerified;

        private String email;
    }

    @Getter
    @Setter
    public static class Profile {
        private String nickname;

        @SerializedName("thumbnail_image_url")
        private String thumbnailImageUrl;

        @SerializedName("profile_image_url")
        private String profileImageUrl;

        @SerializedName("is_default_image")
        private Boolean isDefaultImage;
    }
}

