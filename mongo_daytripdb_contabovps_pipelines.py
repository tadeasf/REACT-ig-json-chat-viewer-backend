def pipelines():
    return {

    "persona_orders": [
    {
        '$sort': {
            'createdAt': -1
        }
    }, {
        '$limit': 50000
    }, {
        '$addFields': {
            'passengersCount': {
                '$size': '$passengers'
            }, 
            'vehiclesCount': {
                '$size': '$vehicles'
            }, 
            'additionalStopCount': {
                '$size': '$customLocations'
            }, 
            'dayMonthYear': {
                '$dateToString': {
                    'format': '%d-%m-%Y', 
                    'date': '$createdAt'
                }
            }
        }
    }, {
        '$unwind': {
            'path': '$discountIds', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$lookup': {
            'from': 'currencyRates', 
            'localField': 'dayMonthYear', 
            'foreignField': 'dayMonthYearString', 
            'as': 'matched_currencyRates'
        }
    }, {
        '$addFields': {
            'matchedCurrencyRate': {
                '$arrayElemAt': [
                    {
                        '$map': {
                            'input': {
                                '$filter': {
                                    'input': '$matched_currencyRates', 
                                    'as': 'currencyRate', 
                                    'cond': {
                                        '$eq': [
                                            '$$currencyRate.type', 0
                                        ]
                                    }
                                }
                            }, 
                            'as': 'filteredRate', 
                            'in': '$$filteredRate.rate'
                        }
                    }, 0
                ]
            }
        }
    }, {
        '$lookup': {
            'from': 'discounts', 
            'localField': 'discountIds', 
            'foreignField': '_id', 
            'as': 'discounts'
        }
    }, {
        '$addFields': {
            'discountsFeeAPIandTA': {
                '$reduce': {
                    'input': {
                        '$filter': {
                            'input': '$discounts', 
                            'as': 'discount', 
                            'cond': {
                                '$in': [
                                    '$$discount.description', [
                                        'API partner discount', 'travel agent discount'
                                    ]
                                ]
                            }
                        }
                    }, 
                    'initialValue': 0.0, 
                    'in': {
                        '$sum': [
                            '$$value', '$$this.fee'
                        ]
                    }
                }
            }
        }
    }, {
        '$group': {
            '_id': '$_id', 
            'root': {
                '$first': '$$ROOT'
            }, 
            'discounts': {
                '$push': '$discounts'
            }
        }
    }, {
        '$replaceRoot': {
            'newRoot': {
                '$mergeObjects': [
                    '$root', {
                        'discounts': '$discounts'
                    }
                ]
            }
        }
    }, {
        '$lookup': {
            'from': 'assignations', 
            'localField': '_id', 
            'foreignField': 'orderId', 
            'as': 'assignation'
        }
    }, {
        '$lookup': {
            'from': 'subsidies', 
            'localField': 'assignation.subsidyIds', 
            'foreignField': '_id', 
            'as': 'subsidies'
        }
    }, {
        '$lookup': {
            'from': 'compensations', 
            'localField': 'assignation.compensationIds', 
            'foreignField': '_id', 
            'as': 'compensations'
        }
    }, {
        '$addFields': {
            'sumOfCompensations': {
                '$reduce': {
                    'input': '$compensations', 
                    'initialValue': 0.0, 
                    'in': {
                        '$sum': [
                            '$$value', '$$this.value'
                        ]
                    }
                }
            }
        }
    }, {
        '$lookup': {
            'from': 'penalties', 
            'localField': 'assignation.penaltyIds', 
            'foreignField': '_id', 
            'as': 'penalties'
        }
    }, {
        '$addFields': {
            'sumOfPenalties': {
                '$reduce': {
                    'input': '$penalties', 
                    'initialValue': 0.0, 
                    'in': {
                        '$sum': [
                            '$$value', '$$this.value'
                        ]
                    }
                }
            }
        }
    }, {
        '$addFields': {
            'sumOfDiscountsFee': {
                '$reduce': {
                    'input': {
                        '$map': {
                            'input': '$discounts', 
                            'as': 'nestedDiscountArray', 
                            'in': {
                                '$cond': [
                                    {
                                        '$ne': [
                                            '$$nestedDiscountArray', []
                                        ]
                                    }, {
                                        '$arrayElemAt': [
                                            '$$nestedDiscountArray.fee', 0.0
                                        ]
                                    }, 0.0
                                ]
                            }
                        }
                    }, 
                    'initialValue': 0.0, 
                    'in': {
                        '$add': [
                            '$$value', '$$this'
                        ]
                    }
                }
            }
        }
    }, {
        '$addFields': {
            'sumOfSubsidies': {
                '$reduce': {
                    'input': '$subsidies', 
                    'initialValue': 0.0, 
                    'in': {
                        '$sum': [
                            '$$value', '$$this.value'
                        ]
                    }
                }
            }
        }
    }, {
        '$lookup': {
            'from': 'users', 
            'localField': 'assignation.userId', 
            'foreignField': '_id', 
            'as': 'drivers'
        }
    }, {
        '$lookup': {
            'from': 'customerFeedbacks', 
            'localField': '_id', 
            'foreignField': 'orderId', 
            'as': 'driverFeedback'
        }
    }, {
        '$addFields': {
            'customLocationsCount': {
                '$size': '$customLocations'
            }, 
            'contentLocationsCount': {
                '$size': '$contentLocations'
            }, 
            'driverRating': {
                '$avg': '$driverFeedback.textScore'
            }
        }
    }, {
        '$addFields': {
            'totalStopsCount': {
                '$sum': [
                    '$customLocationsCount', '$contentLocationsCount'
                ]
            }
        }
    }, {
        '$addFields': {
            'isPool': {
                '$toBool': '$type'
            }
        }
    }, {
        '$addFields': {
            'currencyString': {
                '$toString': '$pricingCurrency'
            }
        }
    }, {
        '$addFields': {
            'pricingCurrencyUsed': {
                '$replaceAll': {
                    'input': '$currencyString', 
                    'find': '0', 
                    'replacement': 'EUR'
                }
            }
        }
    }, {
        '$addFields': {
            'pricingCurrencyUsed': {
                '$replaceAll': {
                    'input': '$pricingCurrencyUsed', 
                    'find': '1', 
                    'replacement': 'USD'
                }
            }
        }
    }, {
        '$addFields': {
            'passengersTypes': {
                '$map': {
                    'input': '$passengers', 
                    'as': 'p', 
                    'in': {
                        '$toString': [
                            '$$p.type'
                        ]
                    }
                }
            }
        }
    }, {
        '$unwind': {
            'path': '$requestHeader', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$addFields': {
            'passenger0': {
                '$arrayElemAt': [
                    '$passengersTypes', 0.0
                ]
            }, 
            'passenger1': {
                '$arrayElemAt': [
                    '$passengersTypes', 1.0
                ]
            }, 
            'passenger2': {
                '$arrayElemAt': [
                    '$passengersTypes', 2.0
                ]
            }, 
            'passenger3': {
                '$arrayElemAt': [
                    '$passengersTypes', 3.0
                ]
            }, 
            'passenger4': {
                '$arrayElemAt': [
                    '$passengersTypes', 4.0
                ]
            }, 
            'passenger5': {
                '$arrayElemAt': [
                    '$passengersTypes', 5.0
                ]
            }, 
            'passenger6': {
                '$arrayElemAt': [
                    '$passengersTypes', 6.0
                ]
            }, 
            'passenger7': {
                '$arrayElemAt': [
                    '$passengersTypes', 7.0
                ]
            }, 
            'passenger8': {
                '$arrayElemAt': [
                    '$passengersTypes', 8.0
                ]
            }
        }
    }, {
        '$addFields': {
            'additionalTravelTime': {
                '$map': {
                    'input': '$customLocations', 
                    'as': 'cl', 
                    'in': {
                        '$toInt': [
                            '$$cl.duration'
                        ]
                    }
                }
            }
        }
    }, {
        '$addFields': {
            'stopTime0': {
                '$arrayElemAt': [
                    '$additionalTravelTime', 0.0
                ]
            }, 
            'stopTime1': {
                '$arrayElemAt': [
                    '$additionalTravelTime', 1.0
                ]
            }, 
            'stopTime2': {
                '$arrayElemAt': [
                    '$additionalTravelTime', 2.0
                ]
            }, 
            'stopTime3': {
                '$arrayElemAt': [
                    '$additionalTravelTime', 3.0
                ]
            }, 
            'stopTime4': {
                '$arrayElemAt': [
                    '$additionalTravelTime', 4.0
                ]
            }, 
            'stopTime5': {
                '$arrayElemAt': [
                    '$additionalTravelTime', 5.0
                ]
            }, 
            'stopTime6': {
                '$arrayElemAt': [
                    '$additionalTravelTime', 6.0
                ]
            }
        }
    }, {
        '$addFields': {
            'travelTime': {
                '$map': {
                    'input': '$contentLocations', 
                    'as': 'cl', 
                    'in': {
                        '$toInt': [
                            '$$cl.duration'
                        ]
                    }
                }
            }
        }
    }, {
        '$addFields': {
            'time0': {
                '$arrayElemAt': [
                    '$travelTime', 0.0
                ]
            }, 
            'time1': {
                '$arrayElemAt': [
                    '$travelTime', 1.0
                ]
            }, 
            'time2': {
                '$arrayElemAt': [
                    '$travelTime', 2.0
                ]
            }, 
            'time3': {
                '$arrayElemAt': [
                    '$travelTime', 3.0
                ]
            }, 
            'time4': {
                '$arrayElemAt': [
                    '$travelTime', 4.0
                ]
            }, 
            'time5': {
                '$arrayElemAt': [
                    '$travelTime', 5.0
                ]
            }, 
            'time6': {
                '$arrayElemAt': [
                    '$travelTime', 6.0
                ]
            }
        }
    }, {
        '$addFields': {
            'totalDuration': {
                '$sum': [
                    '$time0', '$time1', '$time2', '$time3', '$time4', '$time5', '$time6', '$stopTime0', '$stopTime1', '$stopTime2', '$stopTime3', '$stopTime4', '$stopTime5', '$stopTime6'
                ]
            }
        }
    }, {
        '$addFields': {
            'isCustomLocation': {
                '$ne': [
                    {
                        '$size': '$customLocations'
                    }, 0.0
                ]
            }
        }
    }, {
        '$unwind': {
            'path': '$passengers', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$addFields': {
            'extraLuggageCount': {
                '$sum': '$passengers.luggage'
            }
        }
    }, {
        '$addFields': {
            'totalLuggage': {
                '$sum': [
                    '$extraLuggageCount', '$passengersCount'
                ]
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$toString': {
                    '$arrayElemAt': [
                        '$vehicles', 0.0
                    ]
                }
            }
        }
    }, {
        '$addFields': {
            'paymentMethodString': {
                '$toString': '$paymentMethod'
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '0', 
                    'replacement': 'sedan'
                }
            }
        }
    }, {
        '$addFields': {
            'paymentMethodString': {
                '$replaceAll': {
                    'input': '$paymentMethodString', 
                    'find': '0', 
                    'replacement': 'cash'
                }
            }
        }
    }, {
        '$addFields': {
            'paymentMethodString': {
                '$replaceAll': {
                    'input': '$paymentMethodString', 
                    'find': '1', 
                    'replacement': 'prepaid online'
                }
            }
        }
    }, {
        '$addFields': {
            'paymentMethodString': {
                '$replaceAll': {
                    'input': '$paymentMethodString', 
                    'find': '2', 
                    'replacement': 'API'
                }
            }
        }
    }, {
        '$addFields': {
            'paymentMethodString': {
                '$replaceAll': {
                    'input': '$paymentMethodString', 
                    'find': '3', 
                    'replacement': '3'
                }
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '1', 
                    'replacement': 'mpv'
                }
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '2', 
                    'replacement': 'van'
                }
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '3', 
                    'replacement': 'luxury sedan'
                }
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '4', 
                    'replacement': 'shuttle'
                }
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '100', 
                    'replacement': 'sedan lite'
                }
            }
        }
    }, {
        '$match': {
            'passengers.type': 'lead'
        }
    }, {
        '$lookup': {
            'from': 'locations', 
            'localField': 'originLocationId', 
            'foreignField': '_id', 
            'as': 'originLocation'
        }
    }, {
        '$lookup': {
            'from': 'routes', 
            'localField': 'routeId', 
            'foreignField': '_id', 
            'as': 'routes'
        }
    }, {
        '$lookup': {
            'from': 'chargebacks', 
            'localField': '_id', 
            'foreignField': 'orderId', 
            'as': 'chargebacks'
        }
    }, {
        '$lookup': {
            'from': 'payments', 
            'let': {
                'paymentId': '$_id'
            }, 
            'pipeline': [
                {
                    '$match': {
                        '$and': [
                            {
                                '$expr': {
                                    '$eq': [
                                        '$orderId', '$$paymentId'
                                    ]
                                }
                            }, {
                                'fulfilledAt': {
                                    '$ne': None
                                }
                            }, {
                                'failedAt': {
                                    '$eq': None
                                }
                            }, {
                                'chargedBackAt': {
                                    '$eq': None
                                }
                            }
                        ]
                    }
                }
            ], 
            'as': 'payments'
        }
    }, {
        '$addFields': {
            'payments': {
                '$cond': {
                    'if': {
                        '$gt': [
                            {
                                '$size': '$payments'
                            }, 0.0
                        ]
                    }, 
                    'then': {
                        '$arrayElemAt': [
                            '$payments', 0.0
                        ]
                    }, 
                    'else': None
                }
            }
        }
    }, {
        '$unwind': {
            'path': '$payments', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$addFields': {
            'isLite': {
                '$in': [
                    100, '$vehicles'
                ]
            }
        }
    }, {
        '$addFields': {
            'vehiclesFees': {
                '$map': {
                    'input': '$routes.vehicleTypesPricesFees', 
                    'as': 'rt', 
                    'in': {
                        '$map': {
                            'input': '$$rt.fee', 
                            'as': 'f', 
                            'in': {
                                '$toInt': '$$f'
                            }
                        }
                    }
                }
            }
        }
    }, {
        '$addFields': {
            'vehicles': {
                '$map': {
                    'input': '$routes.vehicleTypesPricesFees', 
                    'as': 'rt', 
                    'in': {
                        '$map': {
                            'input': '$$rt.price', 
                            'as': 'f', 
                            'in': {
                                '$toInt': '$$f'
                            }
                        }
                    }
                }
            }
        }
    }, {
        '$unwind': {
            'path': '$vehicles', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$vehiclesFees', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$addFields': {
            'sedanPrice': {
                '$arrayElemAt': [
                    '$vehicles', 0.0
                ]
            }, 
            'mpvPrice': {
                '$arrayElemAt': [
                    '$vehicles', 1.0
                ]
            }, 
            'vanPrice': {
                '$arrayElemAt': [
                    '$vehicles', 2.0
                ]
            }, 
            'luxurySedan': {
                '$arrayElemAt': [
                    '$vehicles', 3.0
                ]
            }
        }
    }, {
        '$addFields': {
            'sedanFee': {
                '$arrayElemAt': [
                    '$vehiclesFees', 0.0
                ]
            }, 
            'mpvFee': {
                '$arrayElemAt': [
                    '$vehiclesFees', 1.0
                ]
            }, 
            'vanFee': {
                '$arrayElemAt': [
                    '$vehiclesFees', 2.0
                ]
            }, 
            'luxurySedanFee': {
                '$arrayElemAt': [
                    '$vehiclesFees', 3.0
                ]
            }
        }
    }, {
        '$addFields': {
            'tollFeeTwice': {
                '$multiply': [
                    {
                        '$arrayElemAt': [
                            '$routes.tollFee', 0.0
                        ]
                    }, 2.0
                ]
            }, 
            'tollPriceTwice': {
                '$multiply': [
                    {
                        '$arrayElemAt': [
                            '$routes.tollPrice', 0.0
                        ]
                    }, 2.0
                ]
            }
        }
    }, {
        '$addFields': {
            'sedanTotalPrice': {
                '$sum': [
                    '$sedanPrice', '$sedanFee', '$routes.additionalFee', '$routes.additionalPrice', '$tollFeeTwice', '$tollPriceTwice'
                ]
            }
        }
    }, {
        '$addFields': {
            'mpvTotalPrice': {
                '$sum': [
                    '$mpvPrice', '$mpvFee', '$routes.additionalFee', '$routes.additionalPrice', '$tollFeeTwice', '$tollPriceTwice'
                ]
            }
        }
    }, {
        '$addFields': {
            'vanTotalPrice': {
                '$sum': [
                    '$vanPrice', '$vanFee', '$routes.additionalFee', '$routes.additionalPrice', '$tollFeeTwice', '$tollPriceTwice'
                ]
            }
        }
    }, {
        '$addFields': {
            'luxurySedanTotalPrice': {
                '$sum': [
                    '$luxurySedan', '$luxurySedanFee', '$routes.additionalFee', '$routes.additionalPrice', '$tollFeeTwice', '$tollPriceTwice'
                ]
            }
        }
    }, {
        '$unwind': {
            'path': '$originLocation', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$originLocation.name', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$lookup': {
            'from': 'countries', 
            'localField': 'pricingCountryId', 
            'foreignField': '_id', 
            'as': 'pricingCountryCollection'
        }
    }, {
        '$lookup': {
            'from': 'countries', 
            'localField': 'originLocation.countryId', 
            'foreignField': '_id', 
            'as': 'originLocationCountry'
        }
    }, {
        '$lookup': {
            'from': 'routes', 
            'localField': 'routeId', 
            'foreignField': '_id', 
            'as': 'route'
        }
    }, {
        '$lookup': {
            'from': 'regions', 
            'localField': 'route.pricingRegionId', 
            'foreignField': '_id', 
            'as': 'region'
        }
    }, {
        '$addFields': {
            'region': {
                '$cond': {
                    'if': {
                        '$or': [
                            {
                                '$eq': [
                                    '$region.englishName', []
                                ]
                            }, {
                                '$eq': [
                                    '$region.englishName', None
                                ]
                            }
                        ]
                    }, 
                    'then': {
                        '$arrayElemAt': [
                            '$pricingCountryCollection.englishName', 0
                        ]
                    }, 
                    'else': {
                        '$arrayElemAt': [
                            '$region.englishName', 0
                        ]
                    }
                }
            }
        }
    }, {
        '$unwind': {
            'path': '$originLocationCountry', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$originLocationCountry.englishName', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$lookup': {
            'from': 'locations', 
            'localField': 'destinationLocationId', 
            'foreignField': '_id', 
            'as': 'destinationLocation'
        }
    }, {
        '$unwind': {
            'path': '$destinationLocation', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$destinationLocation.name', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$lookup': {
            'from': 'countries', 
            'localField': 'destinationLocation.countryId', 
            'foreignField': '_id', 
            'as': 'destinationLocationCountry'
        }
    }, {
        '$unwind': {
            'path': '$destinationLocationCountry', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$destinationLocationCountry.englishName', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$lookup': {
            'from': 'countries', 
            'localField': 'passengers.countryId', 
            'foreignField': '_id', 
            'as': 'leadCountry'
        }
    }, {
        '$unwind': {
            'path': '$leadCountry', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$leadCountry.englishName', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$lookup': {
            'from': 'users', 
            'localField': 'userId', 
            'foreignField': '_id', 
            'as': 'userCollection'
        }
    }, {
        '$unwind': {
            'path': '$userCollection', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$userCollection.affiliatePartner', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$userCollection.travelAgent', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$userCollection.travelAgent.agentId', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$userCollection.travelAgent.ownerId', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$userCollection.travelAgent.approvedAt', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$userCollection.travelAgent.discountCoefficient', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$userCollection.suspiciousCCActivity', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$lookup': {
            'from': 'users', 
            'localField': 'createdBy', 
            'foreignField': '_id', 
            'as': 'createdByUser'
        }
    }, {
        '$lookup': {
            'from': 'countries', 
            'localField': 'userCollection.countryId', 
            'foreignField': '_id', 
            'as': 'travelAgentCountries'
        }
    }, {
        '$unwind': {
            'path': '$travelAgentCountries', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$createdByUser', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$createdByUser.firstName', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$createdByUser.lastName', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$createdByUser.travelAgent', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$createdByUser.travelAgent.agentId', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$lookup': {
            'from': 'users', 
            'localField': 'userId', 
            'foreignField': '_id', 
            'as': 'customerCollection'
        }
    }, {
        '$lookup': {
            'from': 'users', 
            'localField': 'affiliatePartnerId', 
            'foreignField': '_id', 
            'as': 'partnerCollection'
        }
    }, {
        '$unwind': {
            'path': '$customerCollection', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$partnerCollection', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$addFields': {
            'isGroup': {
                '$ifNull': [
                    '$customerCollection.groupIds', []
                ]
            }, 
            'travelAgentCountry': {
                '$cond': {
                    'if': {
                        '$ne': [
                            '$userCollection.travelAgent', None
                        ]
                    }, 
                    'then': '$travelAgentCountries.englishName', 
                    'else': '$$REMOVE'
                }
            }
        }
    }, {
        '$addFields': {
            'isGroup': {
                '$size': '$isGroup'
            }
        }
    }, {
        '$addFields': {
            'passenger0Child': {
                '$cond': {
                    'if': {
                        '$eq': [
                            '$passenger0', 'child'
                        ]
                    }, 
                    'then': True, 
                    'else': False
                }
            }, 
            'passenger1Child': {
                '$cond': {
                    'if': {
                        '$eq': [
                            '$passenger1', 'child'
                        ]
                    }, 
                    'then': True, 
                    'else': False
                }
            }, 
            'passenger2Child': {
                '$cond': {
                    'if': {
                        '$eq': [
                            '$passenger2', 'child'
                        ]
                    }, 
                    'then': True, 
                    'else': False
                }
            }, 
            'passenger3Child': {
                '$cond': {
                    'if': {
                        '$eq': [
                            '$passenger3', 'child'
                        ]
                    }, 
                    'then': True, 
                    'else': False
                }
            }, 
            'passenger4Child': {
                '$cond': {
                    'if': {
                        '$eq': [
                            '$passenger4', 'child'
                        ]
                    }, 
                    'then': True, 
                    'else': False
                }
            }, 
            'passenger5Child': {
                '$cond': {
                    'if': {
                        '$eq': [
                            '$passenger5', 'child'
                        ]
                    }, 
                    'then': True, 
                    'else': False
                }
            }, 
            'passenger6Child': {
                '$cond': {
                    'if': {
                        '$eq': [
                            '$passenger6', 'child'
                        ]
                    }, 
                    'then': True, 
                    'else': False
                }
            }, 
            'passenger7Child': {
                '$cond': {
                    'if': {
                        '$eq': [
                            '$passenger7', 'child'
                        ]
                    }, 
                    'then': True, 
                    'else': False
                }
            }, 
            'passenger8Child': {
                '$cond': {
                    'if': {
                        '$eq': [
                            '$passenger8', 'child'
                        ]
                    }, 
                    'then': True, 
                    'else': False
                }
            }
        }
    }, {
        '$unwind': {
            'path': '$pricingCountryCollection', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$pricingCountryCollection.englishName', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$addFields': {
            'createdAt': {
                '$toDate': '$createdAt'
            }, 
            'sumOfChargebacks': {
                '$reduce': {
                    'input': '$chargebacks', 
                    'initialValue': 0.0, 
                    'in': {
                        '$add': [
                            '$$value', '$$this.amount'
                        ]
                    }
                }
            }
        }
    }, {
        '$addFields': {
            'ownerId': '$userCollection.travelAgent.ownerId'
        }
    }, {
        '$addFields': {
            'travelAgentOwnerId': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$eq': [
                                    '$ownerId', '2c7d5c78-97cd-4796-a493-ca4bc68fde47'
                                ]
                            }, 
                            'then': 'Alexandra Mamrillová'
                        }, {
                            'case': {
                                '$eq': [
                                    '$ownerId', '8fe652a6-209e-4f83-b6b4-ec43c0a74c9c'
                                ]
                            }, 
                            'then': 'Alexandra Mamrillová'
                        }, {
                            'case': {
                                '$eq': [
                                    '$ownerId', '4fb118b3-f562-4a10-8b0c-3d10d9c09950'
                                ]
                            }, 
                            'then': 'Jan Toloch'
                        }
                    ], 
                    'default': '$ownerId'
                }
            }
        }
    }, {
        '$lookup': {
            'from': 'travelData', 
            'let': {
                'originLocationId': '$originLocationId', 
                'destinationLocationId': '$destinationLocationId'
            }, 
            'pipeline': [
                {
                    '$match': {
                        '$expr': {
                            '$and': [
                                {
                                    '$eq': [
                                        '$originId', '$$originLocationId'
                                    ]
                                }, {
                                    '$eq': [
                                        '$destinationId', '$$destinationLocationId'
                                    ]
                                }
                            ]
                        }
                    }
                }
            ], 
            'as': 'matchedData'
        }
    }, {
        '$addFields': {
            'matchedDocument': {
                '$arrayElemAt': [
                    '$matchedData', 0
                ]
            }
        }
    }, {
        '$addFields': {
            'travelDataDuration': '$matchedDocument.duration', 
            'travelDataDistance': '$matchedDocument.distance'
        }
    }, {
        '$addFields': {
            'hasAdditionalStop': {
                '$cond': {
                    'if': {
                        '$gte': [
                            '$additionalStopCount', 1
                        ]
                    }, 
                    'then': True, 
                    'else': False
                }
            }
        }
    }, {
        '$addFields': {
            'leadCountryISO': '$leadCountry.isoCode', 
            'travelAgentId': {
                '$cond': {
                    'if': {
                        '$or': [
                            {
                                '$eq': [
                                    '$userCollection.travelAgent.hostAgencyId', None
                                ]
                            }, {
                                '$eq': [
                                    '$userCollection.travelAgent.hostAgencyId', ''
                                ]
                            }
                        ]
                    }, 
                    'then': '$userCollection.travelAgent.agentId', 
                    'else': None
                }
            }, 
            'travelAgentIdHostAgencies': '$userCollection.travelAgent.hostAgencyId', 
            'travelAgentIdCheck': '$userCollection.travelAgent.agentId'
        }
    }, {
        '$addFields': {
            'vehicles': '$vehicleTypesPricesFees.vehicleType', 
            'originCountry': '$originLocationCountry.englishName', 
            'originLocation': '$originLocation.name', 
            'destinationCountry': '$destinationLocationCountry.englishName', 
            'destinationLocation': '$destinationLocation.name', 
            'leadUserId': '$userId', 
            'leadFullName': {
                '$concat': [
                    '$passengers.firstName', ' ', '$passengers.lastName'
                ]
            }, 
            'leadBirthday': '$passengers.birthdayAt', 
            'leadPhoneNumber': '$passengers.phoneNumber', 
            'leadEmail': '$passengers.email', 
            'leadCountry': '$leadCountry.englishName', 
            'potentialCCFraud': '$userCollection.suspiciousCCActivity', 
            'vehicleType': '$vehiclesString', 
            'travelAgentApprovedAt': '$userCollection.travelAgent.approvedAt', 
            'travelAgentDiscount': {
                '$ifNull': [
                    '$userCollection.travelAgent.discountCoefficient', 0.0
                ]
            }, 
            'routeName': {
                '$concat': [
                    '$originLocation.name', ' ', 'to', ' ', '$destinationLocation.name'
                ]
            }, 
            'createdDepartureDiff': {
                '$divide': [
                    {
                        '$subtract': [
                            '$departureAt', '$createdAt'
                        ]
                    }, 86400000.0
                ]
            }, 
            'orderUserAgent': '$requestHeader.userAgent', 
            'luggageCount': '$totalLuggage', 
            'createdByFullName': {
                '$concat': [
                    '$createdByUser.firstName', ' ', '$createdByUser.lastName'
                ]
            }, 
            'createdByTravelAgent': '$createdByUser.travelAgent.agentId', 
            'customerFullName': {
                '$concat': [
                    '$customerCollection.firstName', ' ', '$customerCollection.lastName'
                ]
            }, 
            'pricingCountryName': '$pricingCountryCollection.englishName', 
            'userCreatedAt': '$userCollection.createdAt', 
            'customerNote': '$customerCollection.customerNote', 
            'customerNote2': '$partnerCollection.customerNote', 
            'userAffiliatePartnerId': '$userCollection.affiliatePartner.partnerId', 
            'paymentType': '$payments.type', 
            'ipAddress': '$requestHeader.remoteAddress', 
            'userAgent': '$requestHeader.userAgent', 
            'customerNoteFixed': {
                '$cond': [
                    {
                        '$or': [
                            {
                                '$regexMatch': {
                                    'input': '$customerNote', 
                                    'regex': 'Toloch'
                                }
                            }, {
                                '$regexMatch': {
                                    'input': '$customerNote2', 
                                    'regex': 'Toloch'
                                }
                            }
                        ]
                    }, 'Jan Toloch', {
                        '$cond': [
                            {
                                '$or': [
                                    {
                                        '$regexMatch': {
                                            'input': '$customerNote', 
                                            'regex': 'Alex'
                                        }
                                    }, {
                                        '$regexMatch': {
                                            'input': '$customerNote2', 
                                            'regex': 'Alex'
                                        }
                                    }
                                ]
                            }, 'Alexandra Mamrillova', '$customerNote'
                        ]
                    }
                ]
            }
        }
    }, {
        '$addFields': {
            'salesRepresentative': {
                '$cond': [
                    {
                        '$or': [
                            {
                                '$eq': [
                                    '$customerNoteFixed', 'Alexandra Mamrillova'
                                ]
                            }, {
                                '$regexMatch': {
                                    'input': '$travelAgentOwnerId', 
                                    'regex': 'Alex'
                                }
                            }
                        ]
                    }, 'Alexandra Mamrillova', {
                        '$cond': [
                            {
                                '$or': [
                                    {
                                        '$eq': [
                                            '$customerNoteFixed', 'Jan Toloch'
                                        ]
                                    }, {
                                        '$regexMatch': {
                                            'input': '$travelAgentOwnerId', 
                                            'regex': 'Toloch'
                                        }
                                    }
                                ]
                            }, 'Jan Toloch', 'Other'
                        ]
                    }
                ]
            }
        }
    }, {
        '$addFields': {
            'isLastMinute24': '$departureDateChangedLessThan24hUntilDeparture', 
            'status': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$acceptedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$acceptedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$confirmedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$confirmedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$draftedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$draftedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 0.0
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$acceptedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$acceptedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$confirmedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$confirmedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 1.0
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 2.0
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$acceptedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$acceptedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$confirmedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$confirmedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 3.0
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 4.0
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$acceptedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$acceptedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$confirmedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$confirmedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$draftedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$draftedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 5.0
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$acceptedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$acceptedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$confirmedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$confirmedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$draftedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$draftedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 6.0
                        }
                    ], 
                    'default': 'not recognized'
                }
            }
        }
    }, {
        '$addFields': {
            'orderStatus': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$eq': [
                                    '$status', 0.0
                                ]
                            }, 
                            'then': 'pending'
                        }, {
                            'case': {
                                '$eq': [
                                    '$status', 1.0
                                ]
                            }, 
                            'then': 'accepted'
                        }, {
                            'case': {
                                '$eq': [
                                    '$status', 2.0
                                ]
                            }, 
                            'then': 'declined'
                        }, {
                            'case': {
                                '$eq': [
                                    '$status', 3.0
                                ]
                            }, 
                            'then': 'confirmed'
                        }, {
                            'case': {
                                '$eq': [
                                    '$status', 4.0
                                ]
                            }, 
                            'then': 'cancelled'
                        }, {
                            'case': {
                                '$eq': [
                                    '$status', 5.0
                                ]
                            }, 
                            'then': 'undefined'
                        }, {
                            'case': {
                                '$eq': [
                                    '$status', 6.0
                                ]
                            }, 
                            'then': 'draft'
                        }
                    ], 
                    'default': 'not recognized'
                }
            }
        }
    }, {
        '$addFields': {
            'b2bMargin': {
                '$subtract': [
                    {
                        '$subtract': [
                            '$totalPrice', '$price'
                        ]
                    }, '$sumOfChargebacks'
                ]
            }, 
            'b2bMarginAlt': {
                '$add': [
                    '$sumOfPenalties', {
                        '$subtract': [
                            {
                                '$subtract': [
                                    {
                                        '$subtract': [
                                            {
                                                '$subtract': [
                                                    '$totalPrice', '$price'
                                                ]
                                            }, '$sumOfChargebacks'
                                        ]
                                    }, '$sumOfSubsidies'
                                ]
                            }, '$sumOfCompensations'
                        ]
                    }
                ]
            }, 
            'userOS': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Windows NT 10\\.0'
                                }
                            }, 
                            'then': 'Windows 10'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Windows NT 6\\.2'
                                }
                            }, 
                            'then': 'Windows 8'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Windows NT 5\\.1'
                                }
                            }, 
                            'then': 'Windows XP'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Windows NT 6\\.3'
                                }
                            }, 
                            'then': 'Windows 8.1'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Windows NT 10\\.0;.*Win64;.*x64'
                                }
                            }, 
                            'then': 'Windows 11'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': '(?:X11;|Linux)'
                                }
                            }, 
                            'then': {
                                '$cond': {
                                    'if': {
                                        '$regexMatch': {
                                            'input': '$userAgent', 
                                            'regex': 'arm'
                                        }
                                    }, 
                                    'then': 'Android', 
                                    'else': 'Android'
                                }
                            }
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Macintosh'
                                }
                            }, 
                            'then': 'macOS'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Android'
                                }
                            }, 
                            'then': 'Android'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': '(iPhone|iPod|iPad).*CPU.*'
                                }
                            }, 
                            'then': 'iOS'
                        }
                    ], 
                    'default': 'Unknown OS'
                }
            }, 
            'userBrowser': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Chrome'
                                }
                            }, 
                            'then': 'Chrome'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Firefox'
                                }
                            }, 
                            'then': 'Firefox'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Safari'
                                }
                            }, 
                            'then': 'Safari'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Edge'
                                }
                            }, 
                            'then': 'Edge'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'MSIE'
                                }
                            }, 
                            'then': 'Internet Explorer'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Brave'
                                }
                            }, 
                            'then': 'Brave'
                        }
                    ], 
                    'default': 'Unknown Browser'
                }
            }, 
            'paymentMethodB2B': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$eq': [
                                    '$paymentMethodString', '3'
                                ]
                            }, 
                            'then': 'paymentMethod3'
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$ifNull': [
                                                            '$travelAgentId', ''
                                                        ]
                                                    }, ''
                                                ]
                                            }, {
                                                '$ne': [
                                                    {
                                                        '$ifNull': [
                                                            '$partnerId', ''
                                                        ]
                                                    }, ''
                                                ]
                                            }, {
                                                '$ne': [
                                                    {
                                                        '$ifNull': [
                                                            '$affiliatePartnerId', ''
                                                        ]
                                                    }, ''
                                                ]
                                            }, {
                                                '$ne': [
                                                    {
                                                        '$ifNull': [
                                                            '$travelAgentIdHostAgencies', ''
                                                        ]
                                                    }, ''
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$ne': [
                                            '$paymentMethodString', '3'
                                        ]
                                    }
                                ]
                            }, 
                            'then': 'B2B'
                        }, {
                            'case': {
                                '$eq': [
                                    '$paymentMethodString', 'prepaid online'
                                ]
                            }, 
                            'then': 'privatePrepaidOnline'
                        }, {
                            'case': {
                                '$eq': [
                                    '$paymentMethodString', 'cash'
                                ]
                            }, 
                            'then': 'privateCash'
                        }
                    ], 
                    'default': 'other'
                }
            }
        }
    }, {
        '$project': {
            'leadCountryISO': 1.0, 
            'salesRepresentative': 1.0, 
            'customerNoteFixed': 1.0, 
            'region': 1, 
            'managementNote': 1, 
            'travelAgentCountry': 1, 
            'matchedCurrencyRate': 1.0, 
            'vehicles': 1.0, 
            'isLite': 1.0, 
            'travelAgentOwnerId': 1.0, 
            'travelAgentIdCheck': 1.0, 
            'ownerId': 1.0, 
            'hasAdditionalStop': 1.0, 
            'travelDataDuration': 1.0, 
            'travelDataDistance': 1.0, 
            'fee': 1.0, 
            'createdAt': 1.0, 
            'departureAt': 1.0, 
            'confirmedAt': 1.0, 
            'cancelledAt': 1.0, 
            'acceptedAt': 1.0, 
            'declinedAt': 1.0, 
            'draftedAt': 1.0, 
            'pricingCurrency': '$pricingCurrencyUsed', 
            'currencyRate': 1.0, 
            'additionalFee': 1.0, 
            'additionalPrice': 1.0, 
            'paymentMethodString': 1.0, 
            'originCountry': 1.0, 
            'originLocation': 1.0, 
            'destinationCountry': 1.0, 
            'destinationLocation': 1.0, 
            'totalStopsCount': 1.0, 
            'isCustomLocation': 1.0, 
            'isPool': 1.0, 
            'createdBy': 1.0, 
            'leadUserId': 1.0, 
            'leadFullName': 1.0, 
            'leadBirthday': 1.0, 
            'leadPhoneNumber': 1.0, 
            'leadEmail': 1.0, 
            'leadCountry': 1.0, 
            'passengersCount': 1.0, 
            'potentialFraud': 1.0, 
            'potentialCCFraud': 1.0, 
            'vehicleType': 1.0, 
            'vehiclesCount': 1.0, 
            'travelAgentId': 1.0, 
            'travelAgentDiscount': 1.0, 
            'travelAgentApprovedAt': 1.0, 
            'partnerId': 1.0, 
            'totalPrice': 1.0, 
            'routeName': 1.0, 
            'totalDuration': 1.0, 
            'isLastMinute24': 1.0, 
            'createdDepartureDiff': 1.0, 
            'orderUserAgent': 1.0, 
            'luggageCount': 1.0, 
            'passenger0': 1.0, 
            'passenger1': 1.0, 
            'passenger2': 1.0, 
            'passenger3': 1.0, 
            'passenger4': 1.0, 
            'passenger5': 1.0, 
            'passenger6': 1.0, 
            'passenger7': 1.0, 
            'passenger8': 1.0, 
            'passenger0Child': 1.0, 
            'passenger1Child': 1.0, 
            'passenger2Child': 1.0, 
            'passenger3Child': 1.0, 
            'passenger4Child': 1.0, 
            'passenger5Child': 1.0, 
            'passenger6Child': 1.0, 
            'passenger7Child': 1.0, 
            'passenger8Child': 1.0, 
            'createdByFullName': 1.0, 
            'createdByTravelAgent': 1.0, 
            'affiliatePartnerId': 1.0, 
            'customerFullName': 1.0, 
            'isGroup': 1.0, 
            'pricingCountryName': 1.0, 
            'routeId': 1.0, 
            'userId': 1.0, 
            'status': 1.0, 
            'orderStatus': 1.0, 
            'userCreatedAt': 1.0, 
            'customerNote': 1.0, 
            'sedanTotalPrice': 1.0, 
            'mpvTotalPrice': 1.0, 
            'vanTotalPrice': 1.0, 
            'luxurySedanTotalPrice': 1.0, 
            'userAffiliatePartnerId': 1.0, 
            'sumOfChargebacks': 1.0, 
            'sumOfPenalties': 1.0, 
            'sumOfCompensations': 1.0, 
            'price': 1.0, 
            'b2bMargin': 1.0, 
            'b2bMarginAlt': 1.0, 
            'isBusinessTrip': 1.0, 
            'paymentType': 1.0, 
            'driverRating': 1.0, 
            'ipAddress': 1.0, 
            'userAgent': 1.0, 
            'sumOfDiscountsFee': 1.0, 
            'sumOfSubsidies': 1.0, 
            'userBrowser': 1.0, 
            'userOS': 1.0, 
            'travelAgentIdHostAgencies': 1.0, 
            'paymentMethodB2B': 1.0, 
            'discountsFeeAPIandTA': 1.0
        }}],
    
    "performancePrices_orders": [
    {
        '$sort': {
            'createdAt': -1
        }
    }, {
        '$limit': 50000
    }, {
        '$lookup': {
            'from': 'discountCodes', 
            'localField': 'discountCode', 
            'foreignField': '_id', 
            'as': 'discountCodes'
        }
    }, {
        '$lookup': {
            'from': 'discounts', 
            'localField': 'discountIds', 
            'foreignField': '_id', 
            'as': 'discounts'
        }
    }, {
        '$lookup': {
            'from': 'locations', 
            'localField': 'originLocationId', 
            'foreignField': '_id', 
            'as': 'originLocationCollection'
        }
    }, {
        '$lookup': {
            'from': 'locations', 
            'localField': 'destinationLocationId', 
            'foreignField': '_id', 
            'as': 'destinationLocationCollection'
        }
    }, {
        '$lookup': {
            'from': 'chargebacks', 
            'localField': '_id', 
            'foreignField': 'orderId', 
            'as': 'chargebacks'
        }
    }, {
        '$lookup': {
            'from': 'countries', 
            'localField': 'originLocationCollection.countryId', 
            'foreignField': '_id', 
            'as': 'originCountryCollection'
        }
    }, {
        '$lookup': {
            'from': 'countries', 
            'localField': 'destinationLocationCollection.countryId', 
            'foreignField': '_id', 
            'as': 'destinationCountryCollection'
        }
    }, {
        '$lookup': {
            'from': 'customerFeedbacks', 
            'localField': '_id', 
            'foreignField': 'orderId', 
            'as': 'feedbacks'
        }
    }, {
        '$lookup': {
            'from': 'assignations', 
            'localField': '_id', 
            'foreignField': 'orderId', 
            'as': 'assignation'
        }
    }, {
        '$lookup': {
            'from': 'subsidies', 
            'localField': 'assignation.subsidyIds', 
            'foreignField': '_id', 
            'as': 'subsidies'
        }
    }, {
        '$lookup': {
            'from': 'users', 
            'localField': 'assignation.userId', 
            'foreignField': '_id', 
            'as': 'drivers'
        }
    }, {
        '$lookup': {
            'from': 'vehicles', 
            'localField': 'drivers._id', 
            'foreignField': 'ownerUserId', 
            'as': 'driversVehicles'
        }
    }, {
        '$lookup': {
            'from': 'vehicleModels', 
            'localField': 'driversVehicles.modelId', 
            'foreignField': '_id', 
            'as': 'driversVehiclesModels'
        }
    }, {
        '$lookup': {
            'from': 'vehicleMakes', 
            'localField': 'driversVehiclesModels.makeId', 
            'foreignField': '_id', 
            'as': 'driversVehiclesModelsMakes'
        }
    }, {
        '$lookup': {
            'from': 'countries', 
            'localField': 'pricingCountryId', 
            'foreignField': '_id', 
            'as': 'pricingCountry'
        }
    }, {
        '$lookup': {
            'from': 'discountCodes', 
            'localField': 'discountCode', 
            'foreignField': '_id', 
            'as': 'discountCodes'
        }
    }, {
        '$lookup': {
            'from': 'payments', 
            'let': {
                'paymentId': '$_id'
            }, 
            'pipeline': [
                {
                    '$match': {
                        '$and': [
                            {
                                '$expr': {
                                    '$eq': [
                                        '$orderId', '$$paymentId'
                                    ]
                                }
                            }, {
                                'fulfilledAt': {
                                    '$ne': None
                                }
                            }, {
                                'failedAt': {
                                    '$eq': None
                                }
                            }, {
                                'chargedBackAt': {
                                    '$eq': None
                                }
                            }
                        ]
                    }
                }
            ], 
            'as': 'payments'
        }
    }, {
        '$lookup': {
            'from': 'payments', 
            'localField': '_id', 
            'foreignField': 'orderId', 
            'as': 'paymentsFull'
        }
    }, {
        '$lookup': {
            'from': 'users', 
            'localField': 'userId', 
            'foreignField': '_id', 
            'as': 'userCollection'
        }
    }, {
        '$lookup': {
            'from': 'users', 
            'localField': 'affiliatePartnerId', 
            'foreignField': '_id', 
            'as': 'partnerCollection'
        }
    }, {
        '$lookup': {
            'from': 'travelData', 
            'let': {
                'originLocationId': '$originLocationId', 
                'destinationLocationId': '$destinationLocationId'
            }, 
            'pipeline': [
                {
                    '$match': {
                        '$expr': {
                            '$and': [
                                {
                                    '$eq': [
                                        '$originId', '$$originLocationId'
                                    ]
                                }, {
                                    '$eq': [
                                        '$destinationId', '$$destinationLocationId'
                                    ]
                                }
                            ]
                        }
                    }
                }
            ], 
            'as': 'matchedData'
        }
    }, {
        '$addFields': {
            'dayMonthYear': {
                '$dateToString': {
                    'format': '%d-%m-%Y', 
                    'date': '$createdAt'
                }
            }
        }
    }, {
        '$lookup': {
            'from': 'currencyRates', 
            'localField': 'dayMonthYear', 
            'foreignField': 'dayMonthYearString', 
            'as': 'matched_currencyRates'
        }
    }, {
        '$lookup': {
            'from': 'routes', 
            'localField': 'routeId', 
            'foreignField': '_id', 
            'as': 'route'
        }
    }, {
        '$lookup': {
            'from': 'regions', 
            'localField': 'route.pricingRegionId', 
            'foreignField': '_id', 
            'as': 'region'
        }
    }, {
        '$addFields': {
            'matchedCurrencyRate': {
                '$arrayElemAt': [
                    {
                        '$map': {
                            'input': {
                                '$filter': {
                                    'input': '$matched_currencyRates', 
                                    'as': 'currencyRate', 
                                    'cond': {
                                        '$eq': [
                                            '$$currencyRate.type', 0
                                        ]
                                    }
                                }
                            }, 
                            'as': 'filteredRate', 
                            'in': '$$filteredRate.rate'
                        }
                    }, 0
                ]
            }
        }
    }, {
        '$addFields': {
            'order': '$$ROOT'
        }
    }, {
        '$addFields': {
            'passengersCount': {
                '$size': '$passengers'
            }, 
            'vehiclesCount': {
                '$size': '$vehicles'
            }, 
            'additionalStopCount': {
                '$size': '$customLocations'
            }, 
            'sumOfChargebacks': {
                '$reduce': {
                    'input': '$chargebacks', 
                    'initialValue': 0.0, 
                    'in': {
                        '$add': [
                            '$$value', '$$this.amount'
                        ]
                    }
                }
            }, 
            'payments': {
                '$cond': {
                    'if': {
                        '$gt': [
                            {
                                '$size': '$payments'
                            }, 0.0
                        ]
                    }, 
                    'then': {
                        '$arrayElemAt': [
                            '$payments', 0.0
                        ]
                    }, 
                    'else': None
                }
            }, 
            'driverRating': {
                '$avg': '$driverFeedback.textScore'
            }, 
            'rating1': {
                '$size': {
                    '$filter': {
                        'input': {
                            '$ifNull': [
                                '$feedbacks', []
                            ]
                        }, 
                        'as': 'feedback', 
                        'cond': {
                            '$eq': [
                                '$$feedback.textScore', 1
                            ]
                        }
                    }
                }
            }, 
            'rating2': {
                '$size': {
                    '$filter': {
                        'input': {
                            '$ifNull': [
                                '$feedbacks', []
                            ]
                        }, 
                        'as': 'feedback', 
                        'cond': {
                            '$eq': [
                                '$$feedback.textScore', 2
                            ]
                        }
                    }
                }
            }, 
            'rating3': {
                '$size': {
                    '$filter': {
                        'input': {
                            '$ifNull': [
                                '$feedbacks', []
                            ]
                        }, 
                        'as': 'feedback', 
                        'cond': {
                            '$eq': [
                                '$$feedback.textScore', 3
                            ]
                        }
                    }
                }
            }, 
            'rating4': {
                '$size': {
                    '$filter': {
                        'input': {
                            '$ifNull': [
                                '$feedbacks', []
                            ]
                        }, 
                        'as': 'feedback', 
                        'cond': {
                            '$eq': [
                                '$$feedback.textScore', 4
                            ]
                        }
                    }
                }
            }, 
            'rating5': {
                '$size': {
                    '$filter': {
                        'input': {
                            '$ifNull': [
                                '$feedbacks', []
                            ]
                        }, 
                        'as': 'feedback', 
                        'cond': {
                            '$eq': [
                                '$$feedback.textScore', 5
                            ]
                        }
                    }
                }
            }
        }
    }, {
        '$addFields': {
            'paymentType': '$payments.type', 
            'vehiclesString': {
                '$toString': {
                    '$arrayElemAt': [
                        '$vehicles', 0.0
                    ]
                }
            }, 
            'driverFirstName0': {
                '$arrayElemAt': [
                    '$drivers.firstName', 0.0
                ]
            }, 
            'driverFirstName1': {
                '$arrayElemAt': [
                    '$drivers.firstName', 1.0
                ]
            }, 
            'driverFirstName2': {
                '$arrayElemAt': [
                    '$drivers.firstName', 2.0
                ]
            }, 
            'driverLastName0': {
                '$arrayElemAt': [
                    '$drivers.lastName', 0.0
                ]
            }, 
            'driverLastName1': {
                '$arrayElemAt': [
                    '$drivers.lastName', 1.0
                ]
            }, 
            'driverLastName2': {
                '$arrayElemAt': [
                    '$drivers.lastName', 2.0
                ]
            }, 
            'driver0Company': {
                '$arrayElemAt': [
                    '$drivers.driversCompany.name', 0.0
                ]
            }, 
            'driver1Company': {
                '$arrayElemAt': [
                    '$drivers.driversCompany.name', 1.0
                ]
            }, 
            'drive2Company': {
                '$arrayElemAt': [
                    '$drivers.driversCompany.name', 2.0
                ]
            }, 
            'vehicleYearOfManufacture0': {
                '$arrayElemAt': [
                    '$driversVehicles.manufactureYear', 0.0
                ]
            }, 
            'vehicleYearOfManufacture1': {
                '$arrayElemAt': [
                    '$driversVehicles.manufactureYear', 1.0
                ]
            }, 
            'vehicleYearOfManufacture2': {
                '$arrayElemAt': [
                    '$driversVehicles.manufactureYear', 2.0
                ]
            }, 
            'vehicleModel0': {
                '$arrayElemAt': [
                    '$driversVehiclesModels.name', 0.0
                ]
            }, 
            'vehicleModel1': {
                '$arrayElemAt': [
                    '$driversVehiclesModels.name', 1.0
                ]
            }, 
            'vehicleModel2': {
                '$arrayElemAt': [
                    '$driversVehiclesModels.name', 2.0
                ]
            }, 
            'vehicleMake0': {
                '$arrayElemAt': [
                    '$driversVehiclesModelsMakes.name', 0.0
                ]
            }, 
            'vehicleMake1': {
                '$arrayElemAt': [
                    '$driversVehiclesModelsMakes.name', 1.0
                ]
            }, 
            'vehicleMake2': {
                '$arrayElemAt': [
                    '$driversVehiclesModelsMakes.name', 2.0
                ]
            }, 
            'sumOfSubsidies': {
                '$reduce': {
                    'input': '$subsidies', 
                    'initialValue': 0.0, 
                    'in': {
                        '$sum': [
                            '$$value', '$$this.value'
                        ]
                    }
                }
            }
        }
    }, {
        '$addFields': {
            'paymentFulfilledAt0': {
                '$arrayElemAt': [
                    '$paymentsFull.fulfilledAt', 0.0
                ]
            }, 
            'paymentFulfilledAt1': {
                '$arrayElemAt': [
                    '$paymentsFull.fulfilledAt', 1.0
                ]
            }, 
            'paymentFulfilledAt2': {
                '$arrayElemAt': [
                    '$paymentsFull.fulfilledAt', 2.0
                ]
            }, 
            'paymentFulfilledAt3': {
                '$arrayElemAt': [
                    '$paymentsFull.fulfilledAt', 3.0
                ]
            }, 
            'paymentFailedAt0': {
                '$arrayElemAt': [
                    '$paymentsFull.failedAt', 0.0
                ]
            }, 
            'paymentFailedAt1': {
                '$arrayElemAt': [
                    '$paymentsFull.failedAt', 1.0
                ]
            }, 
            'paymentFailedAt2': {
                '$arrayElemAt': [
                    '$paymentsFull.failedAt', 2.0
                ]
            }, 
            'paymentFailedAt3': {
                '$arrayElemAt': [
                    '$paymentsFull.failedAt', 3.0
                ]
            }, 
            'paymentChargedBackAt0': {
                '$arrayElemAt': [
                    '$paymentsFull.chargedBackAt', 0.0
                ]
            }, 
            'paymentChargedBackAt1': {
                '$arrayElemAt': [
                    '$paymentsFull.chargedBackAt', 1.0
                ]
            }, 
            'paymentChargedBackAt2': {
                '$arrayElemAt': [
                    '$paymentsFull.chargedBackAt', 2.0
                ]
            }, 
            'paymentChargedBackAt3': {
                '$arrayElemAt': [
                    '$paymentsFull.chargedBackAt', 3.0
                ]
            }, 
            'paymentAmount0': {
                '$arrayElemAt': [
                    '$paymentsFull.amount', 0.0
                ]
            }, 
            'paymentAmount1': {
                '$arrayElemAt': [
                    '$paymentsFull.amount', 1.0
                ]
            }, 
            'paymentAmount2': {
                '$arrayElemAt': [
                    '$paymentsFull.amount', 2.0
                ]
            }, 
            'paymentAmount3': {
                '$arrayElemAt': [
                    '$paymentsFull.amount', 3.0
                ]
            }, 
            'isVisaCampaign': {
                '$cond': [
                    {
                        '$gt': [
                            {
                                '$size': {
                                    '$filter': {
                                        'input': '$discountCodes', 
                                        'as': 'code', 
                                        'cond': {
                                            '$eq': [
                                                '$$code.discountCampaignId', 'b83889ba-c6f9-4493-a2bd-b3a929ce0b31'
                                            ]
                                        }
                                    }
                                }
                            }, 0
                        ]
                    }, True, False
                ]
            }
        }
    }, {
        '$addFields': {
            'feeVisa': {
                '$cond': [
                    {
                        '$eq': [
                            '$isVisaCampaign', True
                        ]
                    }, {
                        '$subtract': [
                            '$fee', {
                                '$arrayElemAt': [
                                    {
                                        '$map': {
                                            'input': {
                                                '$filter': {
                                                    'input': '$discounts', 
                                                    'as': 'discount', 
                                                    'cond': {
                                                        '$eq': [
                                                            '$$discount.description', 'Visa 5%'
                                                        ]
                                                    }
                                                }
                                            }, 
                                            'as': 'filteredDiscount', 
                                            'in': '$$filteredDiscount.price'
                                        }
                                    }, 0
                                ]
                            }
                        ]
                    }, None
                ]
            }, 
            'visaPaymentFailed': {
                '$cond': [
                    {
                        '$and': [
                            {
                                '$eq': [
                                    '$isVisaCampaign', True
                                ]
                            }, {
                                '$ne': [
                                    '$paymentsFull.failedAt', None
                                ]
                            }, {
                                '$or': [
                                    {
                                        '$eq': [
                                            '$paymentsFull.chargedBackedAt', None
                                        ]
                                    }, {
                                        '$eq': [
                                            '$paymentsFull.fulfilledAt', None
                                        ]
                                    }
                                ]
                            }
                        ]
                    }, True, False
                ]
            }, 
            'visaPaymentFulfilled': {
                '$cond': [
                    {
                        '$and': [
                            {
                                '$eq': [
                                    '$isVisaCampaign', True
                                ]
                            }, {
                                '$ne': [
                                    '$paymentsFull.fulfilledAt', None
                                ]
                            }
                        ]
                    }, True, False
                ]
            }
        }
    }, {
        '$addFields': {
            'matchedDocument': {
                '$arrayElemAt': [
                    '$matchedData', 0
                ]
            }
        }
    }, {
        '$addFields': {
            'region': {
                '$cond': {
                    'if': {
                        '$or': [
                            {
                                '$eq': [
                                    '$region.englishName', []
                                ]
                            }, {
                                '$eq': [
                                    '$region.englishName', None
                                ]
                            }
                        ]
                    }, 
                    'then': {
                        '$arrayElemAt': [
                            '$pricingCountry.englishName', 0
                        ]
                    }, 
                    'else': {
                        '$arrayElemAt': [
                            '$region.englishName', 0
                        ]
                    }
                }
            }
        }
    }, {
        '$addFields': {
            'travelDataDuration': '$matchedDocument.duration', 
            'travelDataDistance': '$matchedDocument.distance', 
            'customLocationsCount': {
                '$size': '$customLocations'
            }, 
            'contentLocationsCount': {
                '$size': '$contentLocations'
            }, 
            'isLite': {
                '$in': [
                    100, '$vehicles'
                ]
            }
        }
    }, {
        '$unwind': {
            'path': '$payments', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$partnerCollection', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$originLocationCollection', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$destinationLocationCollection', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$originLocationCollection.countryId', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$destinationLocationCollection.countryId', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$destinationCountryCollection', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$originCountryCollection', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$originLocationCollection'
        }
    }, {
        '$unwind': {
            'path': '$originLocationCollection.name'
        }
    }, {
        '$unwind': {
            'path': '$destinationLocationCollection'
        }
    }, {
        '$unwind': {
            'path': '$destinationLocationCollection.name'
        }
    }, {
        '$unwind': {
            'path': '$requestHeader', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$requestHeader.client', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$requestHeader.userAgent', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$pricingCountry', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$userCollection', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$userCollection.travelAgent', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$userCollection.travelAgent.agentId', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$unwind': {
            'path': '$userCollection.travelAgent.ownerId', 
            'preserveNullAndEmptyArrays': True
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '0', 
                    'replacement': 'sedan'
                }
            }, 
            'totalStopsCount': {
                '$sum': [
                    '$customLocationsCount', '$contentLocationsCount'
                ]
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '1', 
                    'replacement': 'mpv'
                }
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '2', 
                    'replacement': 'van'
                }
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '3', 
                    'replacement': 'luxury sedan'
                }
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '4', 
                    'replacement': 'shuttle'
                }
            }
        }
    }, {
        '$addFields': {
            'vehiclesString': {
                '$replaceAll': {
                    'input': '$vehiclesString', 
                    'find': '100', 
                    'replacement': 'sedan lite'
                }
            }
        }
    }, {
        '$addFields': {
            'driverName0': {
                '$concat': [
                    '$driverFirstName0', ' ', '$driverLastName0'
                ]
            }, 
            'driverName1': {
                '$concat': [
                    '$driverFirstName1', ' ', '$driverLastName1'
                ]
            }, 
            'driverName2': {
                '$concat': [
                    '$driverFirstName2', ' ', '$driverLastName2'
                ]
            }, 
            'hasAdditionalStop': {
                '$cond': {
                    'if': {
                        '$gte': [
                            '$totalStopsCount', 1
                        ]
                    }, 
                    'then': True, 
                    'else': False
                }
            }, 
            'orderStatusString': {
                '$toString': '$status'
            }, 
            'isPool': {
                '$toBool': '$type'
            }, 
            'paymentMethodString': {
                '$toString': '$paymentMethod'
            }, 
            'currencyString': {
                '$toString': '$pricingCurrency'
            }
        }
    }, {
        '$addFields': {
            'status': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$acceptedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$acceptedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$confirmedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$confirmedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$draftedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$draftedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 'pending'
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$acceptedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$acceptedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$confirmedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$confirmedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 'accepted'
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 'declined'
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$acceptedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$acceptedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$confirmedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$confirmedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 'confirmed'
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 'cancelled'
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$acceptedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$acceptedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$confirmedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$confirmedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$draftedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$draftedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 'undefined'
                        }, {
                            'case': {
                                '$and': [
                                    {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$cancelledAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$cancelledAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$declinedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$declinedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$acceptedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$acceptedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$or': [
                                            {
                                                '$eq': [
                                                    {
                                                        '$type': '$confirmedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$eq': [
                                                    '$confirmedAt', None
                                                ]
                                            }
                                        ]
                                    }, {
                                        '$and': [
                                            {
                                                '$ne': [
                                                    {
                                                        '$type': '$draftedAt'
                                                    }, 'missing'
                                                ]
                                            }, {
                                                '$ne': [
                                                    '$draftedAt', None
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }, 
                            'then': 'draft'
                        }
                    ], 
                    'default': 'not recognized'
                }
            }
        }
    }, {
        '$addFields': {
            'paymentMethodString': {
                '$replaceAll': {
                    'input': '$paymentMethodString', 
                    'find': '0', 
                    'replacement': 'cash'
                }
            }
        }
    }, {
        '$addFields': {
            'paymentMethodString': {
                '$replaceAll': {
                    'input': '$paymentMethodString', 
                    'find': '1', 
                    'replacement': 'prepaid online'
                }
            }
        }
    }, {
        '$addFields': {
            'paymentMethodString': {
                '$replaceAll': {
                    'input': '$paymentMethodString', 
                    'find': '2', 
                    'replacement': 'Partners + Travel Agents'
                }
            }
        }
    }, {
        '$addFields': {
            'currencyString': {
                '$replaceAll': {
                    'input': '$currencyString', 
                    'find': '0', 
                    'replacement': 'EUR'
                }
            }
        }
    }, {
        '$addFields': {
            'currencyString': {
                '$replaceAll': {
                    'input': '$currencyString', 
                    'find': '1', 
                    'replacement': 'USD'
                }
            }
        }
    }, {
        '$addFields': {
            'b2bMarginTiotalPricePrice': {
                '$subtract': [
                    '$totalPrice', '$price'
                ]
            }, 
            'partnerFee': {
                '$multiply': [
                    '$totalPrice', 0.1
                ]
            }, 
            'travelAgentId': '$userCollection.travelAgent.agentId', 
            'travelAgentOwnerId': '$userCollection.travelAgent.ownerId', 
            'potentialCCFraud': '$userCollection.suspiciousCCActivity', 
            'potentialFraud': '$potentialFraud'
        }
    }, {
        '$addFields': {
            'travelAgentOwnerId': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$eq': [
                                    '$travelAgentOwnerId', '2c7d5c78-97cd-4796-a493-ca4bc68fde47'
                                ]
                            }, 
                            'then': 'Sašenka Mamrillová'
                        }, {
                            'case': {
                                '$eq': [
                                    '$travelAgentOwnerId', '8fe652a6-209e-4f83-b6b4-ec43c0a74c9c'
                                ]
                            }, 
                            'then': 'Sašenka Mamrillová'
                        }, {
                            'case': {
                                '$eq': [
                                    '$travelAgentOwnerId', '4fb118b3-f562-4a10-8b0c-3d10d9c09950'
                                ]
                            }, 
                            'then': 'Jan Toloch'
                        }
                    ], 
                    'default': '$travelAgentOwnerId'
                }
            }
        }
    }, {
        '$addFields': {
            'b2bMarginPartnerFee': {
                '$subtract': [
                    '$b2bMarginTotalPricePrice', '$partnerFee'
                ]
            }
        }
    }, {
        '$addFields': {
            'b2bMargin': {
                '$subtract': [
                    '$b2bMarginPartnerFee', '$sumOfChargebacks'
                ]
            }, 
            'userAgent': '$requestHeader.userAgent'
        }
    }, {
        '$addFields': {
            'userOS': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Windows NT 10\\.0'
                                }
                            }, 
                            'then': 'Windows 10'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Windows NT 6\\.2'
                                }
                            }, 
                            'then': 'Windows 8'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Windows NT 5\\.1'
                                }
                            }, 
                            'then': 'Windows XP'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Windows NT 6\\.3'
                                }
                            }, 
                            'then': 'Windows 8.1'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Windows NT 10\\.0;.*Win64;.*x64'
                                }
                            }, 
                            'then': 'Windows 11'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': '(?:X11;|Linux)'
                                }
                            }, 
                            'then': {
                                '$cond': {
                                    'if': {
                                        '$regexMatch': {
                                            'input': '$userAgent', 
                                            'regex': 'arm'
                                        }
                                    }, 
                                    'then': 'Android', 
                                    'else': 'Android'
                                }
                            }
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Macintosh'
                                }
                            }, 
                            'then': 'macOS'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Android'
                                }
                            }, 
                            'then': 'Android'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': '(iPhone|iPod|iPad).*CPU.*'
                                }
                            }, 
                            'then': 'iOS'
                        }
                    ], 
                    'default': 'Unknown OS'
                }
            }, 
            'userBrowser': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Chrome'
                                }
                            }, 
                            'then': 'Chrome'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Firefox'
                                }
                            }, 
                            'then': 'Firefox'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Safari'
                                }
                            }, 
                            'then': 'Safari'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Edge'
                                }
                            }, 
                            'then': 'Edge'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'MSIE'
                                }
                            }, 
                            'then': 'Internet Explorer'
                        }, {
                            'case': {
                                '$regexMatch': {
                                    'input': '$userAgent', 
                                    'regex': 'Brave'
                                }
                            }, 
                            'then': 'Brave'
                        }
                    ], 
                    'default': 'Unknown Browser'
                }
            }
        }
    }, {
        '$addFields': {
            'paymentMethodB2B': {
                '$switch': {
                    'branches': [
                        {
                            'case': {
                                '$or': [
                                    {
                                        '$ne': [
                                            {
                                                '$ifNull': [
                                                    '$travelAgentId', ''
                                                ]
                                            }, ''
                                        ]
                                    }, {
                                        '$ne': [
                                            {
                                                '$ifNull': [
                                                    '$partnerId', ''
                                                ]
                                            }, ''
                                        ]
                                    }, {
                                        '$ne': [
                                            {
                                                '$ifNull': [
                                                    '$affiliatePartnerId', ''
                                                ]
                                            }, ''
                                        ]
                                    }
                                ]
                            }, 
                            'then': 'B2B'
                        }, {
                            'case': {
                                '$eq': [
                                    '$paymentMethodString', 'prepaid online'
                                ]
                            }, 
                            'then': 'privatePrepaidOnline'
                        }, {
                            'case': {
                                '$eq': [
                                    '$paymentMethodString', 'cash'
                                ]
                            }, 
                            'then': 'privateCash'
                        }
                    ], 
                    'default': 'other'
                }
            }
        }
    }, {
        '$project': {
            'managementNote': 1.0, 
            'isVisaCampaign': 1.0, 
            'region': 1.0, 
            'feeVisa': 1.0, 
            'visaPaymentFailed': 1.0, 
            'visaPaymentFulfilled': 1.0, 
            'customerEmail': '$userCollection.email', 
            'matchedCurrencyRate': 1.0, 
            'totalStopsCount': 1.0, 
            'customerNote': '$partnerCollection.customerNote', 
            'totalPrice': 1.0, 
            'isLite': 1.0, 
            'hasAdditionalStop': 1.0, 
            'travelDataDuration': 1.0, 
            'travelDataDistance': 1.0, 
            'passengersCount': 1.0, 
            'vehiclesCount': 1.0, 
            'additionalStopCount': 1.0, 
            'partnerId': 1.0, 
            'affiliatePartnerId': 1.0, 
            'travelAgentOwnerId': 1.0, 
            'rating1': 1.0, 
            'rating2': 1.0, 
            'rating3': 1.0, 
            'rating4': 1.0, 
            'rating5': 1.0, 
            'price': 1.0, 
            'fee': 1.0, 
            'discountsPrice': {
                '$reduce': {
                    'input': '$discounts', 
                    'initialValue': 0.0, 
                    'in': {
                        '$sum': [
                            '$$value', '$$this.price'
                        ]
                    }
                }
            }, 
            'discountsFee': {
                '$reduce': {
                    'input': '$discounts', 
                    'initialValue': 0.0, 
                    'in': {
                        '$sum': [
                            '$$value', '$$this.fee'
                        ]
                    }
                }
            }, 
            'discountsFeeAPIandTA': {
                '$reduce': {
                    'input': {
                        '$filter': {
                            'input': '$discounts', 
                            'as': 'discount', 
                            'cond': {
                                '$in': [
                                    '$$discount.description', [
                                        'API partner discount', 'travel agent discount'
                                    ]
                                ]
                            }
                        }
                    }, 
                    'initialValue': 0.0, 
                    'in': {
                        '$sum': [
                            '$$value', '$$this.fee'
                        ]
                    }
                }
            }, 
            'pricingCountryISOCode': {
                '$ifNull': [
                    '$pricingCountry.isoCode', ''
                ]
            }, 
            'createdAt': '$createdAt', 
            'departureAt': '$departureAt', 
            'paymentMethod': '$paymentMethod', 
            'pricingCurrency': '$pricingCurrency', 
            'originCountry': '$originCountryCollection.englishName', 
            'destinationCountry': '$destinationCountryCollection.englishName', 
            'pricingCountryName': '$pricingCountry.englishName', 
            'currencyRate': 1.0, 
            'type': 1.0, 
            'userId': '$order.userId', 
            'sumOfSubsidies': 1.0, 
            'route': {
                '$concat': [
                    '$originLocationCollection.name', ' ', '$destinationLocationCollection.name'
                ]
            }, 
            'originLocation': '$originLocationCollection.name', 
            'destinationLocation': '$destinationLocationCollection.name', 
            'acceptedAt': 1.0, 
            'declinedAt': 1.0, 
            'confirmedAt': 1.0, 
            'cancelledAt': 1.0, 
            'paymentFulfilledAt0': 1.0, 
            'paymentFulfilledAt1': 1.0, 
            'paymentFulfilledAt2': 1.0, 
            'paymentFulfilledAt3': 1.0, 
            'paymentChargedBackAt0': 1.0, 
            'paymentChargedBackAt1': 1.0, 
            'paymentChargedBackAt2': 1.0, 
            'paymentChargedBackAt3': 1.0, 
            'paymentFailedAt0': 1.0, 
            'paymentFailedAt1': 1.0, 
            'paymentFailedAt2': 1.0, 
            'paymentFailedAt3': 1.0, 
            'paymentAmount0': 1.0, 
            'paymentAmount1': 1.0, 
            'paymentAmount2': 1.0, 
            'paymentAmount3': 1.0, 
            'isPaidOut': '$payments.isPaidOut', 
            'driverName0': 1.0, 
            'driverName1': 1.0, 
            'driverName2': 1.0, 
            'driver0Company': 1.0, 
            'driver1Company': 1.0, 
            'driver2Company': 1.0, 
            'routeId': 1.0, 
            'sumOfChargebacks': 1.0, 
            'vehicleYearOfManufacture0': 1.0, 
            'vehicleYearOfManufacture1': 1.0, 
            'travelAgentId': 1.0, 
            'vehicleYearOfManufacture2': 1.0, 
            'vehicleModel0': 1.0, 
            'vehicleModel1': 1.0, 
            'vehicleModel2': 1.0, 
            'vehicleMake0': 1.0, 
            'vehicleMake1': 1.0, 
            'vehicleMake2': 1.0, 
            'isBusinessTrip': 1.0, 
            'paymentType': 1.0, 
            'driverRating': 1.0, 
            'isPool': 1.0, 
            'b2bMargin': 1.0, 
            'b2bMarginTotalPricePrice': 1.0, 
            'partnerFee': 1.0, 
            'b2bMarginPartnerFee': 1.0, 
            'userOS': 1.0, 
            'userBrowser': 1.0, 
            'createdBy': 1.0, 
            'paymentMethodB2B': 1.0, 
            'ipAddress': '$requestHeader.remoteAddress', 
            'userAgent': 1.0, 
            'requestHeaderClientName': '$requestHeader.client.name', 
            'vehicleType': '$vehiclesString', 
            'createdDepartureDiff': {
                '$divide': [
                    {
                        '$subtract': [
                            '$departureAt', '$createdAt'
                        ]
                    }, 86400000.0
                ]
            }, 
            'orderStatus': '$status', 
            'currency': '$currencyString', 
            'travelAgentApprovedAt': '$userCollection.travelAgent.approvedAt', 
            'travelAgentCreatedAt': '$userCollection.travelAgent.createdAt', 
            'potentialCCFraud': 1.0, 
            'potentialFraud': 1.0
        }
    }
],
    
    "driversAssignations_assignations": [
        {"$sort": {"createdAt": -1}},
        {'$limit': 50000},
        {
            "$addFields": {
                "assignation": "$$ROOT"
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "assignation.userId",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {
            "$unwind": "$user"
        },
        {
            "$lookup": {
                "from": "orders",
                "localField": "assignation.orderId",
                "foreignField": "_id",
                "as": "order"
            }
        },
        {
            "$unwind": "$order"
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "order.userId",
                "foreignField": "_id",
                "as": "orderUser"
            }
        },
        {
            "$unwind": "$orderUser"
        },
        {
            "$addFields": {
                "basicPrice": {
                    "$round": {
                        "$sum": [
                            {
                                "$ceil": {
                                    "$multiply": [
                                        2.0,
                                        "$order.tollPrice"
                                    ]
                                }
                            },
                            "$order.additionalPrice"
                        ]
                    }
                }
            }
        },
        {
            "$lookup": {
                "from": "discounts",
                "localField": "order.discountIds",
                "foreignField": "_id",
                "as": "discounts"
            }
        },
        {
            "$lookup": {
                "from": "compensations",
                "localField": "assignation.compensationIds",
                "foreignField": "_id",
                "as": "compensations"
            }
        },
        {
            "$addFields": {
                "sumOfCompensations": {
                    "$reduce": {
                        "input": "$compensations",
                        "initialValue": 0.0,
                        "in": {
                            "$sum": [
                                "$$value",
                                "$$this.value"
                            ]
                        }
                    }
                }
            }
        },
        {
            "$addFields": {
                "status": {
                    "$switch": {
                        "branches": [
                            {
                                "case": {
                                    "$and": [
                                        {
                                            "$or": [
                                                {
                                                    "$eq": [
                                                        {
                                                            "$type": "$assignation.cancelledAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$assignation.cancelledAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "$or": [
                                                {
                                                    "$eq": [
                                                        {
                                                            "$type": "$assignation.declinedAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$assignation.declinedAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "$or": [
                                                {
                                                    "$eq": [
                                                        {
                                                            "$type": "$assignation.acceptedAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$assignation.acceptedAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "then": 0.0
                            },
                            {
                                "case": {
                                    "$and": [
                                        {
                                            "$and": [
                                                {
                                                    "$ne": [
                                                        {
                                                            "$type": "$assignation.acceptedAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$ne": [
                                                        "$assignation.acceptedAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "$or": [
                                                {
                                                    "$eq": [
                                                        {
                                                            "$type": "$assignation.cancelledAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$assignation.cancelledAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "$or": [
                                                {
                                                    "$eq": [
                                                        {
                                                            "$type": "$assignation.declinedAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$assignation.declinedAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "then": 1.0
                            },
                            {
                                "case": {
                                    "$and": [
                                        {
                                            "$and": [
                                                {
                                                    "$ne": [
                                                        {
                                                            "$type": "$assignation.declinedAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$ne": [
                                                        "$assignation.declinedAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "then": 2.0
                            },
                            {
                                "case": {
                                    "$and": [
                                        {
                                            "$and": [
                                                {
                                                    "$ne": [
                                                        {
                                                            "$type": "$assignation.cancelledAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$ne": [
                                                        "$assignation.cancelledAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "then": 3.0
                            }
                        ],
                        "default": "not recognized"
                    }
                }
            }
        },
        {
            "$lookup": {
                "from": "subsidies",
                "localField": "assignation.subsidyIds",
                "foreignField": "_id",
                "as": "subsidies"
            }
        },
        {
            "$addFields": {
                "sumOfSubsidies": {
                    "$reduce": {
                        "input": "$subsidies",
                        "initialValue": 0.0,
                        "in": {
                            "$sum": [
                                "$$value",
                                "$$this.value"
                            ]
                        }
                    }
                }
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "userId",
                "foreignField": "_id",
                "as": "driver"
            }
        },
        {
            "$unwind": {
                "path": "$driver"
            }
        },
        {
            "$lookup": {
                "from": "countries",
                "localField": "driver.countryId",
                "foreignField": "_id",
                "as": "driverCountry"
            }
        },
        {
            "$unwind": {
                "path": "$driverCountry"
            }
        },
        {
            "$lookup": {
                "from": "penalties",
                "localField": "assignation.penaltyIds",
                "foreignField": "_id",
                "as": "penalties"
            }
        },
        {
            "$addFields": {
                "sumOfPenalties": {
                    "$reduce": {
                        "input": "$penalties",
                        "initialValue": 0.0,
                        "in": {
                            "$sum": [
                                "$$value",
                                "$$this.value"
                            ]
                        }
                    }
                }
            }
        },
        {
            "$addFields": {
                "moneyOperations": {
                    "$subtract": [
                        {
                            "$sum": [
                                "$sumOfCompensations",
                                {
                                    "$cond": [
                                        {
                                            "$in": [
                                                "$status",
                                                [
                                                    0.0,
                                                    1.0
                                                ]
                                            ]
                                        },
                                        "$sumOfSubsidies",
                                        0.0
                                    ]
                                }
                            ]
                        },
                        "$sumOfPenalties"
                    ]
                }
            }
        },
        {
            "$addFields": {
                "priceWithoutDiscounts": {
                    "$sum": [
                        {
                            "$sum": [
                                "$basicPrice",
                                {
                                    "$let": {
                                        "vars": {
                                            "let_key_523": {
                                                "$arrayElemAt": [
                                                    {
                                                        "$filter": {
                                                            "input": "$order.vehicleTypesPricesFees",
                                                            "as": "key_522",
                                                            "cond": {
                                                                "$eq": [
                                                                    "$$key_522.vehicleType",
                                                                    "$assignation.vehicleType"
                                                                ]
                                                            }
                                                        }
                                                    },
                                                    0.0
                                                ]
                                            }
                                        },
                                        "in": {
                                            "$sum": [
                                                "$$let_key_523.price"
                                            ]
                                        }
                                    }
                                },
                                {
                                    "$reduce": {
                                        "input": "$order.contentLocations",
                                        "initialValue": 0.0,
                                        "in": {
                                            "$let": {
                                                "vars": {
                                                    "let_key_525": {
                                                        "$arrayElemAt": [
                                                            {
                                                                "$filter": {
                                                                    "input": "$$this.vehicleTypesPricesFees",
                                                                    "as": "key_524",
                                                                    "cond": {
                                                                        "$eq": [
                                                                            "$$key_524.vehicleType",
                                                                            "$assignation.vehicleType"
                                                                        ]
                                                                    }
                                                                }
                                                            },
                                                            0.0
                                                        ]
                                                    }
                                                },
                                                "in": {
                                                    "$sum": [
                                                        "$$value",
                                                        {
                                                            "$ceil": {
                                                                "$multiply": [
                                                                    2.0,
                                                                    "$$this.tollPrice"
                                                                ]
                                                            }
                                                        },
                                                        "$$this.additionalPrice",
                                                        "$$this.entrancePrice",
                                                        "$$this.parkingPrice",
                                                        "$$this.waitingPrice",
                                                        "$$let_key_525.price"
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                },
                                {
                                    "$reduce": {
                                        "input": "$order.customLocations",
                                        "initialValue": 0.0,
                                        "in": {
                                            "$let": {
                                                "vars": {
                                                    "let_key_527": {
                                                        "$arrayElemAt": [
                                                            {
                                                                "$filter": {
                                                                    "input": "$$this.vehicleTypesPricesFees",
                                                                    "as": "key_526",
                                                                    "cond": {
                                                                        "$eq": [
                                                                            "$$key_526.vehicleType",
                                                                            "$assignation.vehicleType"
                                                                        ]
                                                                    }
                                                                }
                                                            },
                                                            0.0
                                                        ]
                                                    }
                                                },
                                                "in": {
                                                    "$sum": [
                                                        "$$value",
                                                        "$$this.waitingPrice",
                                                        "$$let_key_527.price"
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                }
                            ]
                        },
                        "$moneyOperations"
                    ]
                }
            }
        },
        {
            "$addFields": {
                "orderPriceWithoutDiscounts": {
                    "$let": {
                        "vars": {
                            "let_key_528": {
                                "$sum": [
                                    {
                                        "$ceil": {
                                            "$multiply": [
                                                2.0,
                                                "$order.tollPrice"
                                            ]
                                        }
                                    },
                                    "$order.additionalPrice"
                                ]
                            }
                        },
                        "in": {
                            "$reduce": {
                                "input": "$order.vehicles",
                                "initialValue": 0.0,
                                "in": {
                                    "$let": {
                                        "vars": {
                                            "let_key_529": "$$this"
                                        },
                                        "in": {
                                            "$sum": [
                                                "$$value",
                                                {
                                                    "$sum": [
                                                        "$$let_key_528",
                                                        {
                                                            "$let": {
                                                                "vars": {
                                                                    "let_key_531": {
                                                                        "$arrayElemAt": [
                                                                            {
                                                                                "$filter": {
                                                                                    "input": "$order.vehicleTypesPricesFees",
                                                                                    "as": "key_530",
                                                                                    "cond": {
                                                                                        "$eq": [
                                                                                            "$$key_530.vehicleType",
                                                                                            "$$let_key_529"
                                                                                        ]
                                                                                    }
                                                                                }
                                                                            },
                                                                            0.0
                                                                        ]
                                                                    }
                                                                },
                                                                "in": {
                                                                    "$sum": [
                                                                        "$$let_key_531.price"
                                                                    ]
                                                                }
                                                            }
                                                        },
                                                        {
                                                            "$reduce": {
                                                                "input": "$order.contentLocations",
                                                                "initialValue": 0.0,
                                                                "in": {
                                                                    "$let": {
                                                                        "vars": {
                                                                            "let_key_533": {
                                                                                "$arrayElemAt": [
                                                                                    {
                                                                                        "$filter": {
                                                                                            "input": "$$this.vehicleTypesPricesFees",
                                                                                            "as": "key_532",
                                                                                            "cond": {
                                                                                                "$eq": [
                                                                                                    "$$key_532.vehicleType",
                                                                                                    "$$let_key_529"
                                                                                                ]
                                                                                            }
                                                                                        }
                                                                                    },
                                                                                    0.0
                                                                                ]
                                                                            }
                                                                        },
                                                                        "in": {
                                                                            "$sum": [
                                                                                "$$value",
                                                                                {
                                                                                    "$ceil": {
                                                                                        "$multiply": [
                                                                                            2.0,
                                                                                            "$$this.tollPrice"
                                                                                        ]
                                                                                    }
                                                                                },
                                                                                "$$this.additionalPrice",
                                                                                "$$this.entrancePrice",
                                                                                "$$this.parkingPrice",
                                                                                "$$this.waitingPrice",
                                                                                "$$let_key_533.price"
                                                                            ]
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        },
                                                        {
                                                            "$reduce": {
                                                                "input": "$order.customLocations",
                                                                "initialValue": 0.0,
                                                                "in": {
                                                                    "$let": {
                                                                        "vars": {
                                                                            "let_key_535": {
                                                                                "$arrayElemAt": [
                                                                                    {
                                                                                        "$filter": {
                                                                                            "input": "$$this.vehicleTypesPricesFees",
                                                                                            "as": "key_534",
                                                                                            "cond": {
                                                                                                "$eq": [
                                                                                                    "$$key_534.vehicleType",
                                                                                                    "$$let_key_529"
                                                                                                ]
                                                                                            }
                                                                                        }
                                                                                    },
                                                                                    0.0
                                                                                ]
                                                                            }
                                                                        },
                                                                        "in": {
                                                                            "$sum": [
                                                                                "$$value",
                                                                                "$$this.waitingPrice",
                                                                                "$$let_key_535.price"
                                                                            ]
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        {
            "$addFields": {
                "vehiclePriceDiscount": {
                    "$multiply": [
                        {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$orderPriceWithoutDiscounts",
                                        0.0
                                    ]
                                },
                                0.0,
                                {
                                    "$divide": [
                                        "$priceWithoutDiscounts",
                                        "$orderPriceWithoutDiscounts"
                                    ]
                                }
                            ]
                        },
                        {
                            "$reduce": {
                                "input": "$discounts",
                                "initialValue": 0.0,
                                "in": {
                                    "$sum": [
                                        "$$value",
                                        "$$this.price"
                                    ]
                                }
                            }
                        }
                    ]
                }
            }
        },
        {
            "$addFields": {
                "price": {
                    "$round": {
                        "$sum": [
                            {
                                "$sum": [
                                    "$basicPrice",
                                    {
                                        "$let": {
                                            "vars": {
                                                "let_key_537": {
                                                    "$arrayElemAt": [
                                                        {
                                                            "$filter": {
                                                                "input": "$order.vehicleTypesPricesFees",
                                                                "as": "key_536",
                                                                "cond": {
                                                                    "$eq": [
                                                                        "$$key_536.vehicleType",
                                                                        "$assignation.vehicleType"
                                                                    ]
                                                                }
                                                            }
                                                        },
                                                        0.0
                                                    ]
                                                }
                                            },
                                            "in": {
                                                "$sum": [
                                                    "$$let_key_537.price"
                                                ]
                                            }
                                        }
                                    },
                                    {
                                        "$subtract": [
                                            0.0,
                                            "$vehiclePriceDiscount"
                                        ]
                                    },
                                    {
                                        "$reduce": {
                                            "input": "$order.contentLocations",
                                            "initialValue": 0.0,
                                            "in": {
                                                "$let": {
                                                    "vars": {
                                                        "let_key_539": {
                                                            "$arrayElemAt": [
                                                                {
                                                                    "$filter": {
                                                                        "input": "$$this.vehicleTypesPricesFees",
                                                                        "as": "key_538",
                                                                        "cond": {
                                                                            "$eq": [
                                                                                "$$key_538.vehicleType",
                                                                                "$assignation.vehicleType"
                                                                            ]
                                                                        }
                                                                    }
                                                                },
                                                                0.0
                                                            ]
                                                        }
                                                    },
                                                    "in": {
                                                        "$sum": [
                                                            "$$value",
                                                            {
                                                                "$ceil": {
                                                                    "$multiply": [
                                                                        2.0,
                                                                        "$$this.tollPrice"
                                                                    ]
                                                                }
                                                            },
                                                            "$$this.additionalPrice",
                                                            "$$this.entrancePrice",
                                                            "$$this.parkingPrice",
                                                            "$$this.waitingPrice",
                                                            "$$let_key_539.price"
                                                        ]
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "$reduce": {
                                            "input": "$order.customLocations",
                                            "initialValue": 0.0,
                                            "in": {
                                                "$let": {
                                                    "vars": {
                                                        "let_key_541": {
                                                            "$arrayElemAt": [
                                                                {
                                                                    "$filter": {
                                                                        "input": "$$this.vehicleTypesPricesFees",
                                                                        "as": "key_540",
                                                                        "cond": {
                                                                            "$eq": [
                                                                                "$$key_540.vehicleType",
                                                                                "$assignation.vehicleType"
                                                                            ]
                                                                        }
                                                                    }
                                                                },
                                                                0.0
                                                            ]
                                                        }
                                                    },
                                                    "in": {
                                                        "$sum": [
                                                            "$$value",
                                                            "$$this.waitingPrice",
                                                            "$$let_key_541.price"
                                                        ]
                                                    }
                                                }
                                            }
                                        }
                                    }
                                ]
                            },
                            "$moneyOperations"
                        ]
                    }
                }
            }
        },
        {
            "$addFields": {
                "basicFee": {
                    "$round": {
                        "$sum": [
                            {
                                "$multiply": [
                                    2.0,
                                    "$order.tollFee"
                                ]
                            },
                            "$order.additionalFee"
                        ]
                    }
                }
            }
        },
        {
            "$addFields": {
                "feeWithoutDiscounts": {
                    "$subtract": [
                        {
                            "$sum": [
                                "$basicFee",
                                {
                                    "$let": {
                                        "vars": {
                                            "let_key_543": {
                                                "$arrayElemAt": [
                                                    {
                                                        "$filter": {
                                                            "input": "$order.vehicleTypesPricesFees",
                                                            "as": "key_542",
                                                            "cond": {
                                                                "$eq": [
                                                                    "$$key_542.vehicleType",
                                                                    "$assignation.vehicleType"
                                                                ]
                                                            }
                                                        }
                                                    },
                                                    0.0
                                                ]
                                            }
                                        },
                                        "in": {
                                            "$sum": [
                                                "$$let_key_543.fee"
                                            ]
                                        }
                                    }
                                },
                                {
                                    "$reduce": {
                                        "input": "$order.contentLocations",
                                        "initialValue": 0.0,
                                        "in": {
                                            "$let": {
                                                "vars": {
                                                    "let_key_545": {
                                                        "$arrayElemAt": [
                                                            {
                                                                "$filter": {
                                                                    "input": "$$this.vehicleTypesPricesFees",
                                                                    "as": "key_544",
                                                                    "cond": {
                                                                        "$eq": [
                                                                            "$$key_544.vehicleType",
                                                                            "$assignation.vehicleType"
                                                                        ]
                                                                    }
                                                                }
                                                            },
                                                            0.0
                                                        ]
                                                    }
                                                },
                                                "in": {
                                                    "$sum": [
                                                        "$$value",
                                                        {
                                                            "$multiply": [
                                                                2.0,
                                                                "$$this.tollFee"
                                                            ]
                                                        },
                                                        "$$this.additionalFee",
                                                        "$$this.entranceFee",
                                                        "$$this.parkingFee",
                                                        "$$this.waitingFee",
                                                        "$$let_key_545.fee"
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                },
                                {
                                    "$reduce": {
                                        "input": "$order.customLocations",
                                        "initialValue": 0.0,
                                        "in": {
                                            "$let": {
                                                "vars": {
                                                    "let_key_547": {
                                                        "$arrayElemAt": [
                                                            {
                                                                "$filter": {
                                                                    "input": "$$this.vehicleTypesPricesFees",
                                                                    "as": "key_546",
                                                                    "cond": {
                                                                        "$eq": [
                                                                            "$$key_546.vehicleType",
                                                                            "$assignation.vehicleType"
                                                                        ]
                                                                    }
                                                                }
                                                            },
                                                            0.0
                                                        ]
                                                    }
                                                },
                                                "in": {
                                                    "$sum": [
                                                        "$$value",
                                                        "$$this.waitingFee",
                                                        "$$let_key_547.fee"
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                }
                            ]
                        },
                        "$moneyOperations"
                    ]
                }
            }
        },
        {
            "$addFields": {
                "orderFeeWithoutDiscounts": {
                    "$let": {
                        "vars": {
                            "let_key_548": {
                                "$sum": [
                                    {
                                        "$multiply": [
                                            2.0,
                                            "$order.tollFee"
                                        ]
                                    },
                                    "$order.additionalFee"
                                ]
                            }
                        },
                        "in": {
                            "$reduce": {
                                "input": "$order.vehicles",
                                "initialValue": 0.0,
                                "in": {
                                    "$let": {
                                        "vars": {
                                            "let_key_549": "$$this"
                                        },
                                        "in": {
                                            "$sum": [
                                                "$$value",
                                                {
                                                    "$sum": [
                                                        "$$let_key_548",
                                                        {
                                                            "$let": {
                                                                "vars": {
                                                                    "let_key_551": {
                                                                        "$arrayElemAt": [
                                                                            {
                                                                                "$filter": {
                                                                                    "input": "$order.vehicleTypesPricesFees",
                                                                                    "as": "key_550",
                                                                                    "cond": {
                                                                                        "$eq": [
                                                                                            "$$key_550.vehicleType",
                                                                                            "$$let_key_549"
                                                                                        ]
                                                                                    }
                                                                                }
                                                                            },
                                                                            0.0
                                                                        ]
                                                                    }
                                                                },
                                                                "in": {
                                                                    "$sum": [
                                                                        "$$let_key_551.fee"
                                                                    ]
                                                                }
                                                            }
                                                        },
                                                        {
                                                            "$reduce": {
                                                                "input": "$order.contentLocations",
                                                                "initialValue": 0.0,
                                                                "in": {
                                                                    "$let": {
                                                                        "vars": {
                                                                            "let_key_553": {
                                                                                "$arrayElemAt": [
                                                                                    {
                                                                                        "$filter": {
                                                                                            "input": "$$this.vehicleTypesPricesFees",
                                                                                            "as": "key_552",
                                                                                            "cond": {
                                                                                                "$eq": [
                                                                                                    "$$key_552.vehicleType",
                                                                                                    "$$let_key_549"
                                                                                                ]
                                                                                            }
                                                                                        }
                                                                                    },
                                                                                    0.0
                                                                                ]
                                                                            }
                                                                        },
                                                                        "in": {
                                                                            "$sum": [
                                                                                "$$value",
                                                                                {
                                                                                    "$multiply": [
                                                                                        2.0,
                                                                                        "$$this.tollFee"
                                                                                    ]
                                                                                },
                                                                                "$$this.additionalFee",
                                                                                "$$this.entranceFee",
                                                                                "$$this.parkingFee",
                                                                                "$$this.waitingFee",
                                                                                "$$let_key_553.fee"
                                                                            ]
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        },
                                                        {
                                                            "$reduce": {
                                                                "input": "$order.customLocations",
                                                                "initialValue": 0.0,
                                                                "in": {
                                                                    "$let": {
                                                                        "vars": {
                                                                            "let_key_555": {
                                                                                "$arrayElemAt": [
                                                                                    {
                                                                                        "$filter": {
                                                                                            "input": "$$this.vehicleTypesPricesFees",
                                                                                            "as": "key_554",
                                                                                            "cond": {
                                                                                                "$eq": [
                                                                                                    "$$key_554.vehicleType",
                                                                                                    "$$let_key_549"
                                                                                                ]
                                                                                            }
                                                                                        }
                                                                                    },
                                                                                    0.0
                                                                                ]
                                                                            }
                                                                        },
                                                                        "in": {
                                                                            "$sum": [
                                                                                "$$value",
                                                                                "$$this.waitingFee",
                                                                                "$$let_key_555.fee"
                                                                            ]
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        {
            "$addFields": {
                "vehicleFeeDiscount": {
                    "$multiply": [
                        {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$orderFeeWithoutDiscounts",
                                        0.0
                                    ]
                                },
                                0.0,
                                {
                                    "$divide": [
                                        "$feeWithoutDiscounts",
                                        "$orderFeeWithoutDiscounts"
                                    ]
                                }
                            ]
                        },
                        {
                            "$reduce": {
                                "input": "$discounts",
                                "initialValue": 0.0,
                                "in": {
                                    "$sum": [
                                        "$$value",
                                        "$$this.fee"
                                    ]
                                }
                            }
                        }
                    ]
                }
            }
        },
        {
            "$addFields": {
                "fee": {
                    "$round": {
                        "$subtract": [
                            {
                                "$sum": [
                                    "$basicFee",
                                    {
                                        "$let": {
                                            "vars": {
                                                "let_key_557": {
                                                    "$arrayElemAt": [
                                                        {
                                                            "$filter": {
                                                                "input": "$order.vehicleTypesPricesFees",
                                                                "as": "key_556",
                                                                "cond": {
                                                                    "$eq": [
                                                                        "$$key_556.vehicleType",
                                                                        "$assignation.vehicleType"
                                                                    ]
                                                                }
                                                            }
                                                        },
                                                        0.0
                                                    ]
                                                }
                                            },
                                            "in": {
                                                "$sum": [
                                                    "$$let_key_557.fee"
                                                ]
                                            }
                                        }
                                    },
                                    {
                                        "$subtract": [
                                            0.0,
                                            "$vehicleFeeDiscount"
                                        ]
                                    },
                                    {
                                        "$reduce": {
                                            "input": "$order.contentLocations",
                                            "initialValue": 0.0,
                                            "in": {
                                                "$let": {
                                                    "vars": {
                                                        "let_key_559": {
                                                            "$arrayElemAt": [
                                                                {
                                                                    "$filter": {
                                                                        "input": "$$this.vehicleTypesPricesFees",
                                                                        "as": "key_558",
                                                                        "cond": {
                                                                            "$eq": [
                                                                                "$$key_558.vehicleType",
                                                                                "$assignation.vehicleType"
                                                                            ]
                                                                        }
                                                                    }
                                                                },
                                                                0.0
                                                            ]
                                                        }
                                                    },
                                                    "in": {
                                                        "$sum": [
                                                            "$$value",
                                                            {
                                                                "$multiply": [
                                                                    2.0,
                                                                    "$$this.tollFee"
                                                                ]
                                                            },
                                                            "$$this.additionalFee",
                                                            "$$this.entranceFee",
                                                            "$$this.parkingFee",
                                                            "$$this.waitingFee",
                                                            "$$let_key_559.fee"
                                                        ]
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "$reduce": {
                                            "input": "$order.customLocations",
                                            "initialValue": 0.0,
                                            "in": {
                                                "$let": {
                                                    "vars": {
                                                        "let_key_561": {
                                                            "$arrayElemAt": [
                                                                {
                                                                    "$filter": {
                                                                        "input": "$$this.vehicleTypesPricesFees",
                                                                        "as": "key_560",
                                                                        "cond": {
                                                                            "$eq": [
                                                                                "$$key_560.vehicleType",
                                                                                "$assignation.vehicleType"
                                                                            ]
                                                                        }
                                                                    }
                                                                },
                                                                0.0
                                                            ]
                                                        }
                                                    },
                                                    "in": {
                                                        "$sum": [
                                                            "$$value",
                                                            "$$this.waitingFee",
                                                            "$$let_key_561.fee"
                                                        ]
                                                    }
                                                }
                                            }
                                        }
                                    }
                                ]
                            },
                            "$moneyOperations"
                        ]
                    }
                }
            }
        },
        {
            "$lookup": {
                "from": "locations",
                "localField": "order.originLocationId",
                "foreignField": "_id",
                "as": "originLocation"
            }
        },
        {
            "$unwind": "$originLocation"
        },
        {
            "$lookup": {
                "from": "locations",
                "localField": "order.destinationLocationId",
                "foreignField": "_id",
                "as": "destinationLocation"
            }
        },
        {
            "$unwind": "$destinationLocation"
        },
        {
            "$lookup": {
                "from": "locations",
                "localField": "order.contentLocations.locationId",
                "foreignField": "_id",
                "as": "orderLocations"
            }
        },
        {
            "$lookup": {
                "from": "payments",
                "localField": "assignation.orderId",
                "foreignField": "orderId",
                "as": "payments"
            }
        },
        {
            "$sort": {
                "order.departureAt": -1.0
            }
        },
        {
            "$project": {
                "assignationId": "$assignation._id",
                "assignationStatus": {
                    "$switch": {
                        "branches": [
                            {
                                "case": {
                                    "$and": [
                                        {
                                            "$or": [
                                                {
                                                    "$eq": [
                                                        {
                                                            "$type": "$assignation.cancelledAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$assignation.cancelledAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "$or": [
                                                {
                                                    "$eq": [
                                                        {
                                                            "$type": "$assignation.declinedAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$assignation.declinedAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "$or": [
                                                {
                                                    "$eq": [
                                                        {
                                                            "$type": "$assignation.acceptedAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$assignation.acceptedAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "then": 0.0
                            },
                            {
                                "case": {
                                    "$and": [
                                        {
                                            "$and": [
                                                {
                                                    "$ne": [
                                                        {
                                                            "$type": "$assignation.acceptedAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$ne": [
                                                        "$assignation.acceptedAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "$or": [
                                                {
                                                    "$eq": [
                                                        {
                                                            "$type": "$assignation.cancelledAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$assignation.cancelledAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "$or": [
                                                {
                                                    "$eq": [
                                                        {
                                                            "$type": "$assignation.declinedAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$assignation.declinedAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "then": 1.0
                            },
                            {
                                "case": {
                                    "$and": [
                                        {
                                            "$and": [
                                                {
                                                    "$ne": [
                                                        {
                                                            "$type": "$assignation.declinedAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$ne": [
                                                        "$assignation.declinedAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "then": 2.0
                            },
                            {
                                "case": {
                                    "$and": [
                                        {
                                            "$and": [
                                                {
                                                    "$ne": [
                                                        {
                                                            "$type": "$assignation.cancelledAt"
                                                        },
                                                        "missing"
                                                    ]
                                                },
                                                {
                                                    "$ne": [
                                                        "$assignation.cancelledAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "then": 3.0
                            }
                        ],
                        "default": "not recognized"
                    }
                },
                "user": "$user",
                "simpleOrder": {
                        "orderId": "$order._id",
                        "userId": "$order.userId",
                        "userFullName": {
                            "$concat": [
                                "$orderUser.firstName",
                                " ",
                                "$orderUser.lastName"
                            ]
                        },
                    "userEmail": "$orderUser.email",
                    "price": "$price",
                    "fee": "$fee",
                    "pricingCurrency": "$order.pricingCurrency",
                    "paidAmount": {
                            "$reduce": {
                                "input": "$payments",
                                "initialValue": 0.0,
                                "in": {
                                    "$cond": [
                                        {
                                            "$and": [
                                                {
                                                    "$ne": [
                                                        "$$this.fulfilledAt",
                                                        None
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$$this.chargedBackAt",
                                                        None
                                                    ]
                                                },
                                                {
                                                    "$eq": [
                                                        "$$this.failedAt",
                                                        None
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            "$sum": [
                                                "$$value",
                                                "$$this.amount"
                                            ]
                                        },
                                        "$$value"
                                    ]
                                }
                            }
                    },
                    "status": {
                            "$switch": {
                                "branches": [
                                    {
                                        "case": {
                                            "$and": [
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.cancelledAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.cancelledAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.declinedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.declinedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.acceptedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.acceptedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.confirmedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.confirmedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.draftedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.draftedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        "then": 0.0
                                    },
                                    {
                                        "case": {
                                            "$and": [
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.cancelledAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.cancelledAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.declinedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.declinedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$and": [
                                                        {
                                                            "$ne": [
                                                                {
                                                                    "$type": "$order.acceptedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$ne": [
                                                                "$order.acceptedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.confirmedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.confirmedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        "then": 1.0
                                    },
                                    {
                                        "case": {
                                            "$and": [
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.cancelledAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.cancelledAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$and": [
                                                        {
                                                            "$ne": [
                                                                {
                                                                    "$type": "$order.declinedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$ne": [
                                                                "$order.declinedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        "then": 2.0
                                    },
                                    {
                                        "case": {
                                            "$and": [
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.cancelledAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.cancelledAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.declinedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.declinedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$and": [
                                                        {
                                                            "$ne": [
                                                                {
                                                                    "$type": "$order.acceptedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$ne": [
                                                                "$order.acceptedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$and": [
                                                        {
                                                            "$ne": [
                                                                {
                                                                    "$type": "$order.confirmedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$ne": [
                                                                "$order.confirmedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        "then": 3.0
                                    },
                                    {
                                        "case": {
                                            "$and": [
                                                {
                                                    "$and": [
                                                        {
                                                            "$ne": [
                                                                {
                                                                    "$type": "$order.cancelledAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$ne": [
                                                                "$order.cancelledAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        "then": 4.0
                                    },
                                    {
                                        "case": {
                                            "$and": [
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.cancelledAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.cancelledAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.declinedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.declinedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.acceptedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.acceptedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.confirmedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.confirmedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.draftedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.draftedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        "then": 5.0
                                    },
                                    {
                                        "case": {
                                            "$and": [
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.cancelledAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.cancelledAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.declinedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.declinedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.acceptedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.acceptedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$or": [
                                                        {
                                                            "$eq": [
                                                                {
                                                                    "$type": "$order.confirmedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$eq": [
                                                                "$order.confirmedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "$and": [
                                                        {
                                                            "$ne": [
                                                                {
                                                                    "$type": "$order.draftedAt"
                                                                },
                                                                "missing"
                                                            ]
                                                        },
                                                        {
                                                            "$ne": [
                                                                "$order.draftedAt",
                                                                None
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        "then": 6.0
                                    }
                                ],
                                "default": "not recognized"
                            }
                            },
                    "createdAt": "$order.createdAt",
                    "departureAt": "$order.departureAt",
                    "vehicles": "$order.vehicles",
                    "simplePassengers": {
                            "$map": {
                                "input": "$order.passengers",
                                "as": "key_562",
                                "in": {
                                    "type": "$$key_562.type",
                                    "childSeatType": "$$key_562.childSeatType",
                                    "firstName": "$$key_562.firstName",
                                    "lastName": "$$key_562.lastName",
                                    "email": "$$key_562.email",
                                    "luggage": "$$key_562.luggage"
                                }
                            }
                            },
                    "luggage": {
                            "$reduce": {
                                "input": "$order.passengers",
                                "initialValue": [

                                ],
                                "in": {
                                    "$concatArrays": [
                                        "$$value",
                                        "$$this.luggage"
                                    ]
                                }
                            }
                            },
                    "originLocationName": "$originLocation.name",
                    "originLocationId": "$originLocation._id",
                    "originLocationTimeZone": "$originLocation.timezone",
                    "destinationLocationName": "$destinationLocation.name",
                    "destinationLocationId": "$destinationLocation._id",
                    "destinationLocationTimeZone": "$destinationLocation.timezone",
                    "simpleOrderContentLocations": {
                            "$map": {
                                "input": "$order.contentLocations",
                                "as": "key_563",
                                "in": {
                                    "locationId": "$$key_563.locationId",
                                    "order": "$$key_563.order",
                                    "duration": "$$key_563.duration",
                                    "name": {
                                        "$let": {
                                            "vars": {
                                                "let_key_565": {
                                                    "$arrayElemAt": [
                                                        {
                                                            "$filter": {
                                                                "input": "$orderLocations",
                                                                "as": "key_564",
                                                                "cond": {
                                                                    "$eq": [
                                                                        "$$key_564._id",
                                                                        "$$key_563.locationId"
                                                                    ]
                                                                }
                                                            }
                                                        },
                                                        0.0
                                                    ]
                                                }
                                            },
                                            "in": "$$let_key_565.name"
                                        }
                                    },
                                    "countryId": {
                                        "$let": {
                                            "vars": {
                                                "let_key_567": {
                                                    "$arrayElemAt": [
                                                        {
                                                            "$filter": {
                                                                "input": "$orderLocations",
                                                                "as": "key_566",
                                                                "cond": {
                                                                    "$eq": [
                                                                        "$$key_566._id",
                                                                        "$$key_563.locationId"
                                                                    ]
                                                                }
                                                            }
                                                        },
                                                        0.0
                                                    ]
                                                }
                                            },
                                            "in": "$$let_key_567.countryId"
                                        }
                                    },
                                    "imageUrl": {
                                        "$let": {
                                            "vars": {
                                                "let_key_569": {
                                                    "$arrayElemAt": [
                                                        {
                                                            "$filter": {
                                                                "input": "$orderLocations",
                                                                "as": "key_568",
                                                                "cond": {
                                                                    "$eq": [
                                                                        "$$key_568._id",
                                                                        "$$key_563.locationId"
                                                                    ]
                                                                }
                                                            }
                                                        },
                                                        0.0
                                                    ]
                                                }
                                            },
                                            "in": {
                                                "$let": {
                                                    "vars": {
                                                        "let_key_571": {
                                                            "$arrayElemAt": [
                                                                {
                                                                    "$filter": {
                                                                        "input": "$$let_key_569.images",
                                                                        "as": "key_570",
                                                                        "cond": {
                                                                            "$ne": [
                                                                                "$$key_570.url",
                                                                                ""
                                                                            ]
                                                                        }
                                                                    }
                                                                },
                                                                0.0
                                                            ]
                                                        }
                                                    },
                                                    "in": "$$let_key_571.url"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            },
                    "simpleOrderCustomLocations": {
                            "$map": {
                                "input": "$order.customLocations",
                                "as": "key_572",
                                "in": {
                                    "order": "$$key_572.order",
                                    "duration": "$$key_572.duration",
                                    "name": "$$key_572.title",
                                    "position": "$$key_572.position",
                                    "countryId": "$$key_572.countryId"
                                }
                            }
                            },
                    "potentialFraud": "$order.potentialFraud",
                    "paymentMethod": "$order.paymentMethod",
                    "type": "$order.type"
                },
                "createdAt": 1.0,
                "sumOfSubsidies": 1.0,
                "sumOfPenalties": 1.0,
                "discounts": 1.0,
                "sumOfCompensations": 1.0,
                "basicPrice": 1.0,
                "priceWithoutDiscounts": 1.0,
                "orderPriceWithoutDiscounts": 1.0,
                "price": 1.0,
                "basicFee": 1.0,
                "originLocation": 1.0,
                "destinationLocation": 1.0,
                "orderFeeWithoutDiscounts": 1.0,
                "driverName": {
                    "$concat": [
                        "$driver.firstName",
                        " ",
                        "$driver.lastName"
                    ]
                },
                "driverCountry": "$driverCountry.englishName"
            }
        },
        {
            "$project": {
                "_id": 1.0,
                "assignationId": 1.0,
                "assignationStatus": 1.0,
                "orderId": "$simpleOrder.orderId",
                "orderUserId": "$simpleOrder.userId",
                "orderUserFullName": "$simpleOrder.userFullName",
                "orderUserEmail": "$simpleOrder.userEmail",
                "orderPrice": "$simpleOrder.price",
                "orderFee": "$simpleOrder.fee",
                "orderPricingCurrency": "$simpleOrder.pricingCurrency",
                "orderPaidAmount": "$simpleOrder.paidAmount",
                "orderStatus": "$simpleOrder.status",
                "orderCreatedAt": "$simpleOrder.createdAt",
                "orderDepartureAt": "$simpleOrder.departureAt",
                "orderOriginLocationName": "$simpleOrder.originLocationName",
                "orderOriginLocationId": "$simpleOrder.originLocationId",
                "orderOriginLocationTimeZone": "$simpleOrder.originLocationTimeZone",
                "orderDestinationLocationName": "$simpleOrder.destinationLocationName",
                "orderDestinationLocationId": "$simpleOrder.destinationLocationId",
                "orderDestinationLocationTimeZone": "$simpleOrder.destinationLocationTimeZone",
                "orderPotentialFraud": "$simpleOrder.potentialFraud",
                "orderPaymentMethod": "$simpleOrder.paymentMethod",
                "orderType": "$simpleOrder.type",
                "createdAt": 1.0,
                "driverId": "$user._id",
                "orderIdTest": "$order._id",
                "sumOfSubsidies": 1.0,
                "sumOfPenalties": 1.0,
                "sumOfDiscounts": {
                    "$sum": "$discounts.fee"
                },
                "sumOfCompensations": 1.0,
                "basicPrice": 1.0,
                "priceWithoutDiscounts": 1.0,
                "orderPriceWithoutDiscounts": 1.0,
                "price": 1.0,
                "basicFee": 1.0,
                "orderFeeWithoutDiscounts": 1.0,
                "driverCountry": 1.0,
                "driverName": 1.0
            }
        },
        {
            "$addFields": {
                "invoiceFeeAddition": {
                    "$add": [
                        "$orderFeeWithoutDiscounts",
                        "$sumOfPenalties",
                    ]
                },
                "driverUrl": {
                    "$concat": [
                        "https://management.mydaytrip.com/#/driverProfile?userId=",
                        "$driverId"
                    ]
                },
                "orderUrl": {
                    "$concat": [
                        "https://management.mydaytrip.com/#/order?orderId=",
                        "$orderId"
                    ]
                }
            }
        },
        {
            "$addFields": {
                "invoiceFeeSubtract": {
                    "$subtract": [
                        "$invoiceFeeAddition",
                        "$sumOfDiscounts"
                    ]
                }
            }
        },
        {
            "$addFields": {
                "invoiceFee": {
                    "$subtract": [
                        "$invoiceFeeSubtract",
                        "$sumOfSubsidies"
                    ]
                }
            }
        },
        {
            "$project": {
                "_id": 1.0,
                "assignationId": 1.0,
                "assignationStatus": 1.0,
                "orderId": 1.0,
                "orderUserId": 1.0,
                "orderUserFullName": 1.0,
                "orderUserEmail": 1.0,
                "orderPrice": 1.0,
                "orderFee": 1.0,
                "orderPricingCurrency": 1.0,
                "orderPaidAmount": 1.0,
                "orderStatus": 1.0,
                "orderCreatedAt": 1.0,
                "orderDepartureAt": 1.0,
                "orderOriginLocationName": 1.0,
                "orderOriginLocationId": 1.0,
                "orderOriginLocationTimeZone": 1.0,
                "orderDestinationLocationName": 1.0,
                "orderDestinationLocationId": 1.0,
                "orderDestinationLocationTimeZone": 1.0,
                "orderPotentialFraud": 1.0,
                "orderPaymentMethod": 1.0,
                "orderType": 1.0,
                "createdAt": 1.0,
                "driverId": "$user._id",
                "orderIdTest": "$order._id",
                "sumOfSubsidies": 1.0,
                "sumOfPenalties": 1.0,
                "sumOfDiscounts": 1.0,
                "sumOfCompensations": 1.0,
                "basicPrice": 1.0,
                "priceWithoutDiscounts": 1.0,
                "orderPriceWithoutDiscounts": 1.0,
                "driverCountry": 1.0,
                "driverName": 1.0,
                "price": 1.0,
                "basicFee": 1.0,
                "orderFeeWithoutDiscounts": 1.0,
                "invoiceFee": 1.0,
                "driverUrl": 1.0,
                "orderUrl": 1.0
            }
        }
    ],
}