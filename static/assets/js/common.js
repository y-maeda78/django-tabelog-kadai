
AOS.init({
    duration: 1100,
    offset: 100,
    anchorPlacement: 'top-bottom'
});


$(document).ready(function(){
  $('#heroSlick').slick({
    slidesToShow: 1,           
    slidesToScroll: 1,         
    autoplay: true,            // 自動再生を有効化 
    autoplaySpeed: 5000,       // 自動再生の間隔（5000ms = 5秒）
    dots: false,               // 下のページネーションの点を非表示
    arrows: false,             // 左右の矢印を非表示
    fade: true,                // スライドをフェードで切り替える（より背景向け）
    cssEase: 'linear',         // フェード時のアニメーションをスムーズに
    pauseOnFocus: false,       // フォーカス時も自動再生を停止しない
    pauseOnHover: false        // マウスオーバー時も自動再生を停止しない
  });
});

const swiper = new Swiper('.swiper', {
  loop: true,
  effect: "fade",
  speed: 2000,
  allowTouchMove: false,

  autoplay: {
    delay: 4500, // 4.5秒ごとに切り替え
    disableOnInteraction: false,
  },
});

