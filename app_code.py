-- =========================================================
--  TAXI DRIVER SISTEM – baza podatkov
--  Ustvari bazo in tabele (zaženi v MySQL/MariaDB)
-- =========================================================
CREATE DATABASE IF NOT EXISTS taxidriver
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE taxidriver;

-- Tabela uporabnikov (taksisti + administratorji)
CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(191) NOT NULL,
    email VARCHAR(191) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(32) NULL,
    role ENUM('driver','admin') NOT NULL DEFAULT 'driver',
    car_model VARCHAR(191) NULL,
    car_plate VARCHAR(32) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela voženj
CREATE TABLE IF NOT EXISTS rides (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    driver_id BIGINT UNSIGNED NULL,
    passenger_name VARCHAR(191) NOT NULL,
    passenger_phone VARCHAR(32) NOT NULL,
    pickup_address VARCHAR(255) NOT NULL,
    destination_address VARCHAR(255) NOT NULL,
    pickup_lat DECIMAL(10,7) NULL,
    pickup_lng DECIMAL(10,7) NULL,
    dest_lat DECIMAL(10,7) NULL,
    dest_lng DECIMAL(10,7) NULL,
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    distance_km DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    status ENUM('new','accepted','in_progress','finished','cancelled') NOT NULL DEFAULT 'new',
    scheduled_at DATETIME NULL,
    created_at TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (id),
    KEY idx_rides_driver (driver_id),
    KEY idx_rides_status (status),
    CONSTRAINT fk_rides_driver FOREIGN KEY (driver_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela oglasov (avtomatsko vrtenje v aplikaciji)
CREATE TABLE IF NOT EXISTS ads (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    title VARCHAR(191) NOT NULL,
    body TEXT NOT NULL,
    image_url VARCHAR(255) NULL,
    link_url VARCHAR(255) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    impressions INT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dnevnik prikazov oglasov (za statistiko)
CREATE TABLE IF NOT EXISTS ad_impressions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    ad_id BIGINT UNSIGNED NOT NULL,
    driver_id BIGINT UNSIGNED NULL,
    shown_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_ai_ad (ad_id),
    CONSTRAINT fk_ai_ad FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tokeni za mobilno avtentikacijo (Laravel Sanctum)
CREATE TABLE IF NOT EXISTS personal_access_tokens (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    tokenable_type VARCHAR(191) NOT NULL,
    tokenable_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(191) NULL,
    token VARCHAR(64) NOT NULL UNIQUE,
    abilities TEXT NULL,
    last_used_at TIMESTAMP NULL DEFAULT NULL,
    expires_at TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP NULL DEFAULT NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (id),
    KEY idx_pat_tokenable (tokenable_type, tokenable_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Začetni administrator (geslo: admin123 – obvezno spremeni!)
INSERT INTO users (name, email, password, role, is_active, created_at, updated_at)
VALUES ('Administrator', 'admin@taxi.local',
        '$2y$12$e0NRzQZ3mVz1Qe9u5Ff3bOZ8YK7uF0aQ0WJ6xK3nT5pLmN2oPqRrS',
        'admin', 1, NOW(), NOW());

-- Primer oglasa
INSERT INTO ads (title, body, link_url, is_active, created_at, updated_at)
VALUES ('Pranje avtomobilov Sparkle',
        'Vaš taxi zasluži sijaj! 20 % popusta za vse taksiste.',
        'https://primer.si/sparkle', 1, NOW(), NOW());


<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\RideController;
use App\Http\Controllers\Api\AdController;

// Javne poti (brez žetona)
Route::post('/register', [AuthController::class, 'register']);
Route::post('/login',    [AuthController::class, 'login']);

// Zaščitene poti (z Bearer žetonom – Sanctum)
Route::middleware('auth:sanctum')->group(function () {

    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/me',      [AuthController::class, 'me']);

    // Vožnje
    Route::get('/rides',              [RideController::class, 'index']);
    Route::post('/rides',             [RideController::class, 'store']);
    Route::get('/rides/{id}',         [RideController::class, 'show']);
    Route::post('/rides/{id}/accept', [RideController::class, 'accept']);
    Route::post('/rides/{id}/finish', [RideController::class, 'finish']);
    Route::post('/rides/{id}/cancel', [RideController::class, 'cancel']);

    // Avtomatsko dodajanje voženj – aplikacija pošlje vhodne podatke
    // (npr. iz IRG kamere ali uvoženih rezervacij) in API jih samodejno vpiše.
    Route::post('/rides/auto-add', [RideController::class, 'autoAdd']);

    // Oglasi – aplikacija samodejno rotira oglase
    Route::get('/ads/next',               [AdController::class, 'next']);
    Route::post('/ads/{id}/impression',   [AdController::class, 'impression']);
});


<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable;

    protected $fillable = [
        'name',
        'email',
        'password',
        'phone',
        'role',
        'car_model',
        'car_plate',
        'is_active',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    protected function casts(): array
    {
        return [
            'password'  => 'hashed',
            'is_active' => 'boolean',
        ];
    }

    public function rides()
    {
        return $this->hasMany(Ride::class, 'driver_id');
    }
}


<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Ride extends Model
{
    protected $fillable = [
        'driver_id',
        'passenger_name',
        'passenger_phone',
        'pickup_address',
        'destination_address',
        'pickup_lat',
        'pickup_lng',
        'dest_lat',
        'dest_lng',
        'price',
        'distance_km',
        'status',
        'scheduled_at',
    ];

    protected $casts = [
        'price'        => 'decimal:2',
        'distance_km'  => 'decimal:2',
        'scheduled_at' => 'datetime',
    ];

    public function driver()
    {
        return $this->belongsTo(User::class, 'driver_id');
    }
}


<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Ad extends Model
{
    protected $fillable = [
        'title',
        'body',
        'image_url',
        'link_url',
        'is_active',
        'impressions',
    ];

    protected $casts = [
        'is_active' => 'boolean',
    ];
}


<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class AdImpression extends Model
{
    public $timestamps = false;

    protected $fillable = [
        'ad_id',
        'driver_id',
        'shown_at',
    ];

    protected $casts = [
        'shown_at' => 'datetime',
    ];
}


<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

class AuthController extends Controller
{
    public function register(Request $request)
    {
        $data = $request->validate([
            'name'      => 'required|string|max:191',
            'email'     => 'required|email|unique:users,email',
            'password'  => 'required|string|min:6',
            'phone'     => 'nullable|string|max:32',
            'car_model' => 'nullable|string|max:191',
            'car_plate' => 'nullable|string|max:32',
        ]);

        $user = User::create([
            'name'      => $data['name'],
            'email'     => $data['email'],
            'password'  => $data['password'],
            'phone'     => $data['phone'] ?? null,
            'car_model' => $data['car_model'] ?? null,
            'car_plate' => $data['car_plate'] ?? null,
            'role'      => 'driver',
            'is_active' => 1,
        ]);

        $token = $user->createToken('mobile')->plainTextToken;

        return response()->json([
            'token' => $token,
            'user'  => $user,
        ], 201);
    }

    public function login(Request $request)
    {
        $data = $request->validate([
            'email'    => 'required|email',
            'password' => 'required|string',
        ]);

        $user = User::where('email', $data['email'])->first();

        if (! $user || ! Hash::check($data['password'], $user->password)) {
            throw ValidationException::withMessages([
                'email' => 'Napačen e-poštni naslov ali geslo.',
            ]);
        }

        if (! $user->is_active) {
            return response()->json(['message' => 'Račun je deaktiviran.'], 403);
        }

        $token = $user->createToken('mobile')->plainTextToken;

        return response()->json([
            'token' => $token,
            'user'  => $user,
        ]);
    }

    public function logout(Request $request)
    {
        $request->user()->currentAccessToken()->delete();

        return response()->json(['message' => 'Uspešno odjavljen.']);
    }

    public function me(Request $request)
    {
        return response()->json($request->user());
    }
}


<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Ride;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

class RideController extends Controller
{
    /**
     * Seznam voženj: nove (razpoložljive) + vožnje prijavljenega voznika.
     */
    public function index(Request $request)
    {
        $driverId = $request->user()->id;

        $newRides = Ride::whereNull('driver_id')
            ->where('status', 'new')
            ->orderBy('created_at', 'desc')
            ->limit(50)
            ->get();

        $myRides = Ride::where('driver_id', $driverId)
            ->whereIn('status', ['accepted', 'in_progress', 'finished'])
            ->orderBy('created_at', 'desc')
            ->limit(100)
            ->get();

        return response()->json([
            'new' => $newRides,
            'my'  => $myRides,
        ]);
    }

    public function show(Request $request, int $id)
    {
        $ride = Ride::with('driver')->findOrFail($id);

        return response()->json($ride);
    }

    /**
     * Ročno dodajanje vožnje (voznik sam vnese podatke).
     */
    public function store(Request $request)
    {
        $data = $request->validate([
            'passenger_name'      => 'required|string|max:191',
            'passenger_phone'     => 'required|string|max:32',
            'pickup_address'      => 'required|string|max:255',
            'destination_address' => 'required|string|max:255',
            'pickup_lat'          => 'nullable|numeric',
            'pickup_lng'          => 'nullable|numeric',
            'dest_lat'            => 'nullable|numeric',
            'dest_lng'            => 'nullable|numeric',
            'price'               => 'required|numeric|min:0',
            'distance_km'         => 'nullable|numeric|min:0',
            'scheduled_at'        => 'nullable|date',
        ]);

        $ride = Ride::create($data + [
            'driver_id' => $request->user()->id,
            'status'    => 'accepted',
        ]);

        return response()->json($ride, 201);
    }

    /**
     * AVTOMATSKO DODAJANJE VOŽENJ.
     *
     * Mobilna aplikacija (WorkManager) periodično pošlje seznam novih
     * naročil (npr. iz centralne dispečerije, IRG kamere ali SMS
     * preusmerjanja). API jih samodejno vnese, če še ne obstajajo
     * (deduplikacija po telefonski številki + naslovu + času).
     */
    public function autoAdd(Request $request)
    {
        $request->validate([
            'rides'                 => 'required|array|min:1',
            'rides.*.passenger_name'      => 'required|string|max:191',
            'rides.*.passenger_phone'     => 'required|string|max:32',
            'rides.*.pickup_address'      => 'required|string|max:255',
            'rides.*.destination_address' => 'required|string|max:255',
            'rides.*.price'               => 'nullable|numeric|min:0',
            'rides.*.distance_km'         => 'nullable|numeric|min:0',
            'rides.*.scheduled_at'        => 'nullable|date',
        ]);

        $driverId = $request->user()->id;
        $created  = 0;
        $skipped  = 0;

        foreach ($request->input('rides') as $input) {
            $exists = Ride::where('passenger_phone', $input['passenger_phone'])
                ->where('pickup_address', $input['pickup_address'])
                ->where('destination_address', $input['destination_address'])
                ->whereDate('created_at', today())
                ->exists();

            if ($exists) {
                $skipped++;
                continue;
            }

            Ride::create([
                'driver_id'           => $driverId,
                'passenger_name'      => $input['passenger_name'],
                'passenger_phone'     => $input['passenger_phone'],
                'pickup_address'      => $input['pickup_address'],
                'destination_address' => $input['destination_address'],
                'pickup_lat'          => $input['pickup_lat'] ?? null,
                'pickup_lng'          => $input['pickup_lng'] ?? null,
                'dest_lat'            => $input['dest_lat'] ?? null,
                'dest_lng'            => $input['dest_lng'] ?? null,
                'price'               => $input['price'] ?? 0,
                'distance_km'         => $input['distance_km'] ?? 0,
                'status'              => 'accepted',
                'scheduled_at'        => $input['scheduled_at'] ?? now(),
            ]);

            $created++;
        }

        Log::info('Avtomatsko dodajanje voženj', [
            'driver_id' => $driverId,
            'created'   => $created,
            'skipped'   => $skipped,
        ]);

        return response()->json([
            'message' => 'Avtomatsko dodajanje končano.',
            'created' => $created,
            'skipped' => $skipped,
        ]);
    }

    public function accept(Request $request, int $id)
    {
        return DB::transaction(function () use ($request, $id) {
            $ride = Ride::where('id', $id)
                ->where('status', 'new')
                ->lockForUpdate()
                ->firstOrFail();

            $ride->update([
                'driver_id' => $request->user()->id,
                'status'    => 'accepted',
            ]);

            return response()->json($ride);
        });
    }

    public function finish(Request $request, int $id)
    {
        $ride = Ride::where('id', $id)
            ->where('driver_id', $request->user()->id)
            ->whereIn('status', ['accepted', 'in_progress'])
            ->firstOrFail();

        $ride->update(['status' => 'finished']);

        return response()->json($ride);
    }

    public function cancel(Request $request, int $id)
    {
        $ride = Ride::where('id', $id)
            ->where('driver_id', $request->user()->id)
            ->whereIn('status', ['accepted', 'in_progress'])
            ->firstOrFail();

        $ride->update([
            'status'    => 'cancelled',
            'driver_id' => null,
        ]);

        return response()->json($ride);
    }
}


<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Ad;
use App\Models\AdImpression;
use Illuminate\Http\Request;

class AdController extends Controller
{
    /**
     * AVTOMATSKO OGLAŠEVANJE.
     *
     * Vrne naslednji aktivni oglas po strategiji najmanj prikazov
     * (round-robin na podlagi števila impresij), tako da se oglasi
     * samodejno vrtenijo brez ročnih nastavitev v aplikaciji.
     */
    public function next(Request $request)
    {
        $ad = Ad::where('is_active', 1)
            ->orderBy('impressions', 'asc')
            ->orderBy('id', 'asc')
            ->first();

        if (! $ad) {
            return response()->json(['message' => 'Ni aktivnih oglasov.'], 404);
        }

        return response()->json($ad);
    }

    /**
     * Voznikova aplikacija javi, da je bil oglas prikazan.
     * API poveča števec impresij in zapiše dnevnik.
     */
    public function impression(Request $request, int $id)
    {
        $ad = Ad::findOrFail($id);

        $ad->increment('impressions');

        AdImpression::create([
            'ad_id'     => $ad->id,
            'driver_id' => $request->user()->id,
            'shown_at'  => now(),
        ]);

        return response()->json(['message' => 'Impresija zabeležena.']);
    }
}


APP_NAME=TaxiDriver
APP_ENV=production
APP_KEY=
APP_DEBUG=false
APP_URL=https://tvoj-domen.si

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=taxidriver
DB_USERNAME=tvoj_uporabnik
DB_PASSWORD=tvoje_geslo

SANCTUM_STATEFUL_DOMAINS=tvoj-domen.si


plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}

android {
    namespace 'si.taxidriver.app'
    compileSdk 34

    defaultConfig {
        applicationId "si.taxidriver.app"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = '17'
    }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.11.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
    implementation 'androidx.recyclerview:recyclerview:1.3.2'
    implementation 'androidx.work:work-runtime-ktx:2.9.0'
    implementation 'androidx.lifecycle:lifecycle-runtime-ktx:2.7.0'

    // Retrofit + Gson za komunikacijo z Laravel API
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.squareup.okhttp3:logging-interceptor:4.12.0'
}


<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />

    <application
        android:name=".TaxiApp"
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:usesCleartextTraffic="true"
        android:theme="@style/Theme.TaxiDriver">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <activity
            android:name=".HomeActivity"
            android:exported="false" />

    </application>
</manifest>


<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">TaxiDriver</string>
    <string name="prijava">Prijava</string>
    <string name="email">E-pošta</string>
    <string name="geslo">Geslo</string>
    <string name="voznik_panely">Panel voznika</string>
    <string name="nove_voznje">Nove vožnje</string>
    <string name="moje_voznje">Moje vožnje</string>
    <string name="sprejmi">Sprejmi vožnjo</string>
    <string name="zakljuci">Zaključi vožnjo</string>
    <string name="dodaj_voznjo">Dodaj vožnjo</string>
    <string name="avtomatsko_dodajanje">Avtomatsko dodajanje vklopljeno</string>
</resources>


package si.taxidriver.app

import android.app.Application
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import si.taxidriver.app.workers.AutoRideWorker
import si.taxidriver.app.workers.AdRotationWorker
import java.util.concurrent.TimeUnit

class TaxiApp : Application() {

    override fun onCreate() {
        super.onCreate()

        val workManager = WorkManager.getInstance(this)

        // AVTOMATSKO DODAJANJE VOŽENJ:
        // vsakih 15 minut pridobi/sinhronizira naročila in jih samodejno vpiše.
        val autoRideRequest = PeriodicWorkRequestBuilder<AutoRideWorker>(15, TimeUnit.MINUTES)
            .build()

        workManager.enqueueUniquePeriodicWork(
            "auto_rides",
            ExistingPeriodicWorkPolicy.KEEP,
            autoRideRequest
        )

        // AVTOMATSKO OGLAŠEVANJE:
        // vsakih 30 minut pridobi naslednji oglas (round-robin) in ga shrani
        // za prikaz ob zagonu aplikacije ter javi impresijo.
        val adRequest = PeriodicWorkRequestBuilder<AdRotationWorker>(30, TimeUnit.MINUTES)
            .build()

        workManager.enqueueUniquePeriodicWork(
            "ad_rotation",
            ExistingPeriodicWorkPolicy.KEEP,
            adRequest
        )
    }
}


package si.taxidriver.app.data

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object ApiClient {

    // Spremeni na naslov svojega Laravel strežnika!
    private const val BASE_URL = "https://tvoj-domen.si/api/"

    var authToken: String? = null

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val authInterceptor = okhttp3.Interceptor { chain ->
        val builder = chain.request().newBuilder()
        authToken?.let { builder.addHeader("Authorization", "Bearer $it") }
        chain.proceed(builder.build())
    }

    private val client = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .addInterceptor(authInterceptor)
        .build()

    val api: ApiInterface by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiInterface::class.java)
    }
}


package si.taxidriver.app.data

import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import si.taxidriver.app.data.models.Ad
import si.taxidriver.app.data.models.LoginRequest
import si.taxidriver.app.data.models.LoginResponse
import si.taxidriver.app.data.models.Ride
import si.taxidriver.app.data.models.RidesResponse
import si.taxidriver.app.data.models.AutoAddRequest
import si.taxidriver.app.data.models.AutoAddResponse
import si.taxidriver.app.data.models.MessageResponse

interface ApiInterface {

    @POST("login")
    fun login(@Body body: LoginRequest): Call<LoginResponse>

    @GET("rides")
    fun getRides(): Call<RidesResponse>

    @POST("rides/{id}/accept")
    fun acceptRide(@Path("id") rideId: Long): Call<Ride>

    @POST("rides/{id}/finish")
    fun finishRide(@Path("id") rideId: Long): Call<Ride>

    @POST("rides/{id}/cancel")
    fun cancelRide(@Path("id") rideId: Long): Call<Ride>

    @POST("rides/auto-add")
    fun autoAddRides(@Body body: AutoAddRequest): Call<AutoAddResponse>

    @GET("ads/next")
    fun nextAd(): Call<Ad>

    @POST("ads/{id}/impression")
    fun reportImpression(@Path("id") adId: Long): Call<MessageResponse>
}


package si.taxidriver.app.data.models

import com.google.gson.annotations.SerializedName

data class LoginRequest(
    val email: String,
    val password: String
)

data class LoginResponse(
    val token: String,
    val user: User
)

data class User(
    val id: Long,
    val name: String,
    val email: String,
    @SerializedName("phone") val phone: String?,
    @SerializedName("car_model") val carModel: String?,
    @SerializedName("car_plate") val carPlate: String?,
    val role: String
)

data class Ride(
    val id: Long,
    @SerializedName("driver_id") val driverId: Long?,
    @SerializedName("passenger_name") val passengerName: String,
    @SerializedName("passenger_phone") val passengerPhone: String,
    @SerializedName("pickup_address") val pickupAddress: String,
    @SerializedName("destination_address") val destinationAddress: String,
    val price: Double,
    @SerializedName("distance_km") val distanceKm: Double,
    val status: String,
    @SerializedName("scheduled_at") val scheduledAt: String?
)

data class RidesResponse(
    val new: List<Ride>,
    val my: List<Ride>
)

data class AutoAddRequest(
    val rides: List<AutoRideItem>
)

data class AutoRideItem(
    @SerializedName("passenger_name") val passengerName: String,
    @SerializedName("passenger_phone") val passengerPhone: String,
    @SerializedName("pickup_address") val pickupAddress: String,
    @SerializedName("destination_address") val destinationAddress: String,
    val price: Double,
    @SerializedName("distance_km") val distanceKm: Double,
    @SerializedName("scheduled_at") val scheduledAt: String?
)

data class AutoAddResponse(
    val message: String,
    val created: Int,
    val skipped: Int
)

data class Ad(
    val id: Long,
    val title: String,
    val body: String,
    @SerializedName("image_url") val imageUrl: String?,
    @SerializedName("link_url") val linkUrl: String?
)

data class MessageResponse(
    val message: String
)


package si.taxidriver.app.storage

import android.content.Context

object SessionManager {

    private const val PREFS = "taxi_prefs"
    private const val KEY_TOKEN = "token"
    private const val KEY_LAST_AD_ID = "last_ad_id"

    fun saveToken(context: Context, token: String) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_TOKEN, token)
            .apply()
    }

    fun getToken(context: Context): String? {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(KEY_TOKEN, null)
    }

    fun clear(context: Context) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .clear()
            .apply()
    }

    fun saveLastAdId(context: Context, adId: Long) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putLong(KEY_LAST_AD_ID, adId)
            .apply()
    }

    fun getLastAdId(context: Context): Long {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getLong(KEY_LAST_AD_ID, -1L)
    }
}


package si.taxidriver.app

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import si.taxidriver.app.data.ApiClient
import si.taxidriver.app.data.models.LoginRequest
import si.taxidriver.app.data.models.LoginResponse
import si.taxidriver.app.storage.SessionManager
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class MainActivity : AppCompatActivity() {

    private lateinit var etEmail: EditText
    private lateinit var etPassword: EditText
    private lateinit var btnLogin: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Če uporabnik že ima žeton, preskoči prijavo
        val savedToken = SessionManager.getToken(this)
        if (!savedToken.isNullOrEmpty()) {
            ApiClient.authToken = savedToken
            startActivity(Intent(this, HomeActivity::class.java))
            finish()
            return
        }

        setContentView(R.layout.activity_main)

        etEmail = findViewById(R.id.etEmail)
        etPassword = findViewById(R.id.etPassword)
        btnLogin = findViewById(R.id.btnLogin)

        btnLogin.setOnClickListener {
            val email = etEmail.text.toString().trim()
            val password = etPassword.text.toString().trim()

            if (email.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Vpiši e-pošto in geslo.", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            prijaviUporabnika(email, password)
        }
    }

    private fun prijaviUporabnika(email: String, password: String) {
        btnLogin.isEnabled = false

        ApiClient.api.login(LoginRequest(email, password)).enqueue(object : Callback<LoginResponse> {
            override fun onResponse(call: Call<LoginResponse>, response: Response<LoginResponse>) {
                btnLogin.isEnabled = true

                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    ApiClient.authToken = body.token
                    SessionManager.saveToken(this@MainActivity, body.token)

                    Toast.makeText(
                        this@MainActivity,
                        "Pozdravljen, ${body.user.name}!",
                        Toast.LENGTH_SHORT
                    ).show()

                    startActivity(Intent(this@MainActivity, HomeActivity::class.java))
                    finish()
                } else {
                    Toast.makeText(
                        this@MainActivity,
                        "Prijava ni uspela. Preveri podatke.",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }

            override fun onFailure(call: Call<LoginResponse>, t: Throwable) {
                btnLogin.isEnabled = true
                Toast.makeText(
                    this@MainActivity,
                    "Napaka omrežja: ${t.message}",
                    Toast.LENGTH_LONG
                ).show()
            }
        })
    }
}


<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:gravity="center"
    android:padding="24dp">

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="TaxiDriver"
        android:textSize="28sp"
        android:textStyle="bold"
        android:layout_marginBottom="32dp" />

    <EditText
        android:id="@+id/etEmail"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="@string/email"
        android:inputType="textEmailAddress" />

    <EditText
        android:id="@+id/etPassword"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="@string/geslo"
        android:inputType="textPassword"
        android:layout_marginTop="12dp" />

    <Button
        android:id="@+id/btnLogin"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="@string/prijava"
        android:layout_marginTop="24dp" />

</LinearLayout>


package si.taxidriver.app

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import si.taxidriver.app.data.ApiClient
import si.taxidriver.app.data.models.Ride
import si.taxidriver.app.data.models.RidesResponse
import si.taxidriver.app.storage.SessionManager
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class HomeActivity : AppCompatActivity() {

    private lateinit var rvNewRides: RecyclerView
    private lateinit var rvMyRides: RecyclerView
    private lateinit var tvAdTitle: TextView
    private lateinit var tvAdBody: TextView
    private lateinit var adBanner: LinearLayout
    private lateinit var btnLogout: Button
    private lateinit var btnManualRide: Button

    private val newRidesList: MutableList<Ride> = mutableListOf()
    private val myRidesList: MutableList<Ride> = mutableListOf()
    private lateinit var newRidesAdapter: RideAdapter
    private lateinit var myRidesAdapter: RideAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_home)

        rvNewRides = findViewById(R.id.rvNewRides)
        rvMyRides = findViewById(R.id.rvMyRides)
        tvAdTitle = findViewById(R.id.tvAdTitle)
        tvAdBody = findViewById(R.id.tvAdBody)
        adBanner = findViewById(R.id.adBanner)
        btnLogout = findViewById(R.id.btnLogout)
        btnManualRide = findViewById(R.id.btnManualRide)

        newRidesAdapter = RideAdapter(newRidesList) { ride -> prikaziDialogSprejmi(ride) }
        myRidesAdapter = RideAdapter(myRidesList) { ride -> prikaziDialogZakljuci(ride) }

        rvNewRides.layoutManager = LinearLayoutManager(this)
        rvNewRides.adapter = newRidesAdapter

        rvMyRides.layoutManager = LinearLayoutManager(this)
        rvMyRides.adapter = myRidesAdapter

        btnLogout.setOnClickListener {
            SessionManager.clear(this)
            ApiClient.authToken = null
            startActivity(Intent(this, MainActivity::class.java))
            finish()
        }

        btnManualRide.setOnClickListener { prikaziDialogRocnaVoznja() }

        naloziVoznje()
        prikaziOglas()
    }

    override fun onResume() {
        super.onResume()
        naloziVoznje()
    }

    private fun naloziVoznje() {
        ApiClient.api.getRides().enqueue(object : Callback<RidesResponse> {
            override fun onResponse(call: Call<RidesResponse>, response: Response<RidesResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!

                    newRidesList.clear()
                    newRidesList.addAll(body.new)
                    newRidesAdapter.notifyDataSetChanged()

                    myRidesList.clear()
                    myRidesList.addAll(body.my)
                    myRidesAdapter.notifyDataSetChanged()
                }
            }

            override fun onFailure(call: Call<RidesResponse>, t: Throwable) {
                Toast.makeText(
                    this@HomeActivity,
                    "Napaka pri nalaganju voženj: ${t.message}",
                    Toast.LENGTH_SHORT
                ).show()
            }
        })
    }

    private fun prikaziDialogSprejmi(ride: Ride) {
        AlertDialog.Builder(this)
            .setTitle("Nova vožnja")
            .setMessage(
                "Potnik: ${ride.passengerName}\n" +
                "Telefon: ${ride.passengerPhone}\n" +
                "Vzponišče: ${ride.pickupAddress}\n" +
                "Cilj: ${ride.destinationAddress}\n" +
                "Cena: ${ride.price} €"
            )
            .setPositiveButton("Sprejmi") { _, _ -> sprejmiVoznjo(ride) }
            .setNegativeButton("Prekliči", null)
            .show()
    }

    private fun sprejmiVoznjo(ride: Ride) {
        ApiClient.api.acceptRide(ride.id).enqueue(object : Callback<Ride> {
            override fun onResponse(call: Call<Ride>, response: Response<Ride>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@HomeActivity, "Vožnja sprejeta!", Toast.LENGTH_SHORT).show()
                    // Takoj pokliči potnika
                    val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:${ride.passengerPhone}"))
                    startActivity(intent)
                    naloziVoznje()
                }
            }

            override fun onFailure(call: Call<Ride>, t: Throwable) {
                Toast.makeText(this@HomeActivity, "Napaka: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun prikaziDialogZakljuci(ride: Ride) {
        AlertDialog.Builder(this)
            .setTitle("Vožnja #${ride.id}")
            .setMessage("Stanje: ${ride.status}. Želiš jo zaključiti?")
            .setPositiveButton("Zaključi") { _, _ ->
                ApiClient.api.finishRide(ride.id).enqueue(object : Callback<Ride> {
                    override fun onResponse(call: Call<Ride>, response: Response<Ride>) {
                        Toast.makeText(this@HomeActivity, "Vožnja zaključena.", Toast.LENGTH_SHORT).show()
                        naloziVoznje()
                    }

                    override fun onFailure(call: Call<Ride>, t: Throwable) {
                        Toast.makeText(this@HomeActivity, "Napaka: ${t.message}", Toast.LENGTH_SHORT).show()
                    }
                })
            }
            .setNegativeButton("Prekliči vožnjo") { _, _ ->
                ApiClient.api.cancelRide(ride.id).enqueue(object : Callback<Ride> {
                    override fun onResponse(call: Call<Ride>, response: Response<Ride>) {
                        Toast.makeText(this@HomeActivity, "Vožnja preklicana.", Toast.LENGTH_SHORT).show()
                        naloziVoznje()
                    }

                    override fun onFailure(call: Call<Ride>, t: Throwable) {
                        Toast.makeText(this@HomeActivity, "Napaka: ${t.message}", Toast.LENGTH_SHORT).show()
                    }
                })
            }
            .show()
    }

    private fun prikaziDialogRocnaVoznja() {
        val dialogView = layoutInflater.inflate(R.layout.dialog_add_ride, null)

        val etIme = dialogView.findViewById<android.widget.EditText>(R.id.etPassengerName)
        val etTelefon = dialogView.findViewById<android.widget.EditText>(R.id.etPassengerPhone)
        val etVzponisce = dialogView.findViewById<android.widget.EditText>(R.id.etPickup)
        val etCilj = dialogView.findViewById<android.widget.EditText>(R.id.etDestination)
        val etCena = dialogView.findViewById<android.widget.EditText>(R.id.etPrice)

        AlertDialog.Builder(this)
            .setTitle("Ročna vožnja")
            .setView(dialogView)
            .setPositiveButton("Shrani") { _, _ ->
                val ride = si.taxidriver.app.data.models.AutoRideItem(
                    passengerName = etIme.text.toString(),
                    passengerPhone = etTelefon.text.toString(),
                    pickupAddress = etVzponisce.text.toString(),
                    destinationAddress = etCilj.text.toString(),
                    price = etCena.text.toString().toDoubleOrNull() ?: 0.0,
                    distanceKm = 0.0,
                    scheduledAt = null
                )

                ApiClient.api.autoAddRides(
                    si.taxidriver.app.data.models.AutoAddRequest(listOf(ride))
                ).enqueue(object : retrofit2.Callback<si.taxidriver.app.data.models.AutoAddResponse> {
                    override fun onResponse(
                        call: retrofit2.Call<si.taxidriver.app.data.models.AutoAddResponse>,
                        response: retrofit2.Response<si.taxidriver.app.data.models.AutoAddResponse>
                    ) {
                        Toast.makeText(this@HomeActivity, "Vožnja shranjena.", Toast.LENGTH_SHORT).show()
                        naloziVoznje()
                    }

                    override fun onFailure(
                        call: retrofit2.Call<si.taxidriver.app.data.models.AutoAddResponse>,
                        t: Throwable
                    ) {
                        Toast.makeText(this@HomeActivity, "Napaka: ${t.message}", Toast.LENGTH_SHORT).show()
                    }
                })
            }
            .setNegativeButton("Prekliči", null)
            .show()
    }

    /**
     * AVTOMATSKO OGLAŠEVANJE – prikaže trenutni oglas (round-robin).
     * Oglas se tudi samodejno osveži vsakih 30 minut prek AdRotationWorker.
     */
    private fun prikaziOglas() {
        ApiClient.api.nextAd().enqueue(object : Callback<si.taxidriver.app.data.models.Ad> {
            override fun onResponse(
                call: Call<si.taxidriver.app.data.models.Ad>,
                response: Response<si.taxidriver.app.data.models.Ad>
            ) {
                if (response.isSuccessful && response.body() != null) {
                    val ad = response.body()!!

                    tvAdTitle.text = ad.title
                    tvAdBody.text = ad.body
                    adBanner.visibility = View.VISIBLE

                    // Javi impresijo strežniku (za rotacijo in statistiko)
                    ApiClient.api.reportImpression(ad.id)
                        .enqueue(object : Callback<si.taxidriver.app.data.models.MessageResponse> {
                            override fun onResponse(
                                call: Call<si.taxidriver.app.data.models.MessageResponse>,
                                response: Response<si.taxidriver.app.data.models.MessageResponse>
                            ) { /* nižjeprioritetno – brez dejanja */ }

                            override fun onFailure(
                                call: Call<si.taxidriver.app.data.models.MessageResponse>,
                                t: Throwable
                            ) { /* nižjeprioritetno – brez dejanja */ }
                        })

                    // Klik na oglas odpre povezavo oglasilca
                    adBanner.setOnClickListener {
                        ad.linkUrl?.let { url ->
                            try {
                                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                            } catch (_: Exception) { /* neveljavna povezava */ }
                        }
                    }
                } else {
                    adBanner.visibility = View.GONE
                }
            }

            override fun onFailure(call: Call<si.taxidriver.app.data.models.Ad>, t: Throwable) {
                adBanner.visibility = View.GONE
            }
        })
    }
}


package si.taxidriver.app

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import si.taxidriver.app.data.models.Ride

class RideAdapter(
    private val rides: List<Ride>,
    private val onClick: (Ride) -> Unit
) : RecyclerView.Adapter<RideAdapter.RideViewHolder>() {

    inner class RideViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val tvPassenger: TextView = itemView.findViewById(R.id.tvPassenger)
        val tvRoute: TextView = itemView.findViewById(R.id.tvRoute)
        val tvPriceStatus: TextView = itemView.findViewById(R.id.tvPriceStatus)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RideViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_ride, parent, false)
        return RideViewHolder(view)
    }

    override fun onBindViewHolder(holder: RideViewHolder, position: Int) {
        val ride = rides[position]

        holder.tvPassenger.text = "${ride.passengerName} – ${ride.passengerPhone}"
        holder.tvRoute.text = "${ride.pickupAddress} → ${ride.destinationAddress}"
        holder.tvPriceStatus.text = "${ride.price} € | ${ride.status}"

        holder.itemView.setOnClickListener { onClick(ride) }
    }

    override fun getItemCount(): Int = rides.size
}


<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="16dp">

    <!-- AVTOMATSKI OGLAŠEVALNI PAS -->
    <LinearLayout
        android:id="@+id/adBanner"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:background="#FFF3CD"
        android:padding="12dp"
        android:visibility="gone">

        <TextView
            android:id="@+id/tvAdTitle"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:textStyle="bold"
            android:textSize="16sp" />

        <TextView
            android:id="@+id/tvAdBody"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:textSize="14sp" />
    </LinearLayout>

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/nove_voznje"
        android:textStyle="bold"
        android:textSize="18sp"
        android:layout_marginTop="16dp" />

    <androidx.recyclerview.widget.RecyclerView
        android:id="@+id/rvNewRides"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1" />

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="@string/moje_voznje"
        android:textStyle="bold"
        android:textSize="18sp"
        android:layout_marginTop="16dp" />

    <androidx.recyclerview.widget.RecyclerView
        android:id="@+id/rvMyRides"
        android:layout_width="match_parent"
        android:layout_height="0dp"
        android:layout_weight="1" />

    <Button
        android:id="@+id/btnManualRide"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="@string/dodaj_voznjo"
        android:layout_marginTop="8dp" />

    <Button
        android:id="@+id/btnLogout"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Odjava"
        android:layout_marginTop="8dp" />

</LinearLayout>


<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:orientation="vertical"
    android:padding="12dp"
    android:background="?android:attr/selectableItemBackground">

    <TextView
        android:id="@+id/tvPassenger"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:textStyle="bold"
        android:textSize="16sp" />

    <TextView
        android:id="@+id/tvRoute"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:textSize="14sp" />

    <TextView
        android:id="@+id/tvPriceStatus"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:textSize="13sp"
        android:textColor="#666666" />

</LinearLayout>


<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:orientation="vertical"
    android:padding="16dp">

    <EditText
        android:id="@+id/etPassengerName"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="Ime potnika" />

    <EditText
        android:id="@+id/etPassengerPhone"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="Telefon potnika"
        android:inputType="phone" />

    <EditText
        android:id="@+id/etPickup"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="Naslov vzponišča" />

    <EditText
        android:id="@+id/etDestination"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="Cilj" />

    <EditText
        android:id="@+id/etPrice"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="Cena (€)"
        android:inputType="numberDecimal" />

</LinearLayout>


package si.taxidriver.app.workers

import android.content.Context
import androidx.work.Worker
import androidx.work.WorkerParameters
import si.taxidriver.app.data.ApiClient
import si.taxidriver.app.data.models.AutoAddRequest
import si.taxidriver.app.data.models.AutoAddResponse
import si.taxidriver.app.data.models.AutoRideItem
import si.taxidriver.app.storage.SessionManager
import com.google.gson.Gson

/**
 * AVTOMATSKO DODAJANJE VOŽENJ.
 *
 * WorkManager periodično (vsakih 15 minut) izvede naslednje:
 *  1. Pridobi vozniške naročila iz lokalne vrste (SharedPreferences
 *     "pending_rides") – te vanese centralna dispečerija, SMS-napovednik
 *     ali IRG kamera, ki jih vpiše v JSON.
 *  2. Pošlje jih na API /rides/auto-add, kjer strežnik preveri
 *     deduplikacijo in jih samodejno vpiše v bazo.
 *  3. Po uspešni oddaji lokalno vrsto izprazni.
 */
class AutoRideWorker(
    context: Context,
    params: WorkerParameters
) : Worker(context, params) {

    override fun doWork(): Result {
        val token = SessionManager.getToken(applicationContext)

        if (token.isNullOrEmpty()) {
            return Result.success() // uporabnik ni prijavljen – nič ne delamo
        }

        ApiClient.authToken = token

        val prefs = applicationContext.getSharedPreferences("pending_rides", Context.MODE_PRIVATE)
        val json = prefs.getString("rides", null) ?: return Result.success()

        return try {
            val gson = Gson()
            val items: Array<AutoRideItem> = gson.fromJson(json, Array<AutoRideItem>::class.java)

            if (items.isEmpty()) {
                return Result.success()
            }

            val response = ApiClient.api.autoAddRides(AutoAddRequest(items.toList())).execute()

            if (response.isSuccessful && response.body() != null) {
                val body: AutoAddResponse = response.body()!!

                // Vrsta izpraznimo šele po uspešni oddaji
                if (body.created > 0 || body.skipped > 0) {
                    prefs.edit().remove("rides").apply()
                }

                return Result.success()
            } else {
                // Strežnik ni sprejel – poskusimo znova ob naslednjem ciklu
                Result.retry()
            }
        } catch (e: Exception) {
            Result.retry()
        }
    }
}


package si.taxidriver.app.workers

import android.content.Context
import androidx.work.Worker
import androidx.work.WorkerParameters
import si.taxidriver.app.data.ApiClient
import si.taxidriver.app.data.models.Ad
import si.taxidriver.app.data.models.MessageResponse
import si.taxidriver.app.storage.SessionManager
import retrofit2.Response

/**
 * AVTOMATSKO OGLAŠEVANJE.
 *
 * WorkManager vsakih 30 minut:
 *  1. Pridobi naslednji oglas iz API-ja (strežnik vrne oglas z
 *     najmanj prikazi – samodejna round-robin rotacija).
 *  2. Shrani oglas lokalno, da ga HomeActivity prikaže ob naslednjem
 *     odpiranju aplikacije brez omrežnega klica.
 *  3. Takoj javi impresijo, da rotacija ostane natančna.
 */
class AdRotationWorker(
    context: Context,
    params: WorkerParameters
) : Worker(context, params) {

    override fun doWork(): Result {
        val token = SessionManager.getToken(applicationContext)

        if (token.isNullOrEmpty()) {
            return Result.success()
        }

        ApiClient.authToken = token

        return try {
            val adResponse: Response<Ad> = ApiClient.api.nextAd().execute()

            if (adResponse.isSuccessful && adResponse.body() != null) {
                val ad = adResponse.body()!!

                // Shrani oglas za prikaz ob naslednjem zagonu aplikacije
                applicationContext.getSharedPreferences("cached_ad", Context.MODE_PRIVATE)
                    .edit()
                    .putLong("ad_id", ad.id)
                    .putString("ad_title", ad.title)
                    .putString("ad_body", ad.body)
                    .putString("ad_link", ad.linkUrl ?: "")
                    .apply()

                // Javi impresijo, da strežnik pravilno rotira oglase
                try {
                    ApiClient.api.reportImpression(ad.id).execute()
                } catch (_: Exception) {
                    // impresija ni kritična – oglas je že pripravljen
                }

                Result.success()
            } else {
                Result.retry()
            }
        } catch (e: Exception) {
            Result.retry()
        }
    }
}
